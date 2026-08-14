/*
 * ============================================================
 * ESTUFA DE FILAMENTO - INTEGRADA AO SERVIDOR DO FABLAB
 * ============================================================
 * A estufa continua com controle local autônomo (histerese,
 * botões físicos, painel web local), mas agora sincroniza com
 * o servidor Django do FabLab:
 *
 *   - A cada SYNC_INTERVALO ms envia POST JSON para
 *     /estufa/api/telemetria/ com as leituras dos 5 sensores.
 *   - A resposta traz "modo_desejado": se for diferente do modo
 *     atual, a estufa troca de modo (comando vindo do site).
 *   - Ao apertar um botão físico, envia sync imediato com
 *     origem_botao=true — o botão tem prioridade no servidor.
 *
 * Como a estufa está atrás do NAT do laboratório, é sempre ela
 * quem inicia a conexão (polling). O servidor nunca precisa
 * alcançar o ESP32 diretamente.
 *
 * CONFIGURAÇÃO:
 *   1. Cadastre a estufa no admin do site (/admin/estufa/estufa/)
 *      e copie o token gerado para ESTUFA_TOKEN abaixo.
 *   2. Ajuste SERVER_URL para o endereço público do servidor.
 *   3. Ajuste o Wi-Fi.
 */

#include <DHT.h>
#include <WiFi.h>
#include <ArduinoOTA.h>
#include <WebServer.h>
#include <HTTPClient.h>
#include <WiFiClientSecure.h>

// ================= CONFIGURAÇÃO =================

// --- REDE WI-FI DO LABORATÓRIO ---
const char* ssid = "Fabnet";
const char* password = "SUA_SENHA_AQUI";

// --- SERVIDOR DJANGO DO FABLAB ---
// Use https:// se o site tiver certificado; http:// caso contrário.
const char* SERVER_URL = "https://SEU_SERVIDOR_DA_FACULDADE/estufa/api/telemetria/";
// Token gerado no admin do site (campo "token" da estufa cadastrada)
const char* ESTUFA_TOKEN = "COLE_O_TOKEN_AQUI";

// Intervalo de sincronização com o servidor (30 s)
const unsigned long SYNC_INTERVALO = 30000;

// ================= HARDWARE =================

WebServer server(80);

// --- PINOS DE CONTROLE ---
#define LAMPADA_PIN 5
#define COOLER_PIN 6
#define BOTAO_SECAGEM 2
#define BOTAO_ARMAZEM 3

// --- SENSORES DHT22 ---
#define DHTTYPE DHT22
DHT dht1(0, DHTTYPE); DHT dht2(1, DHTTYPE); DHT dht3(4, DHTTYPE); DHT dht4(7, DHTTYPE); DHT dht5(10, DHTTYPE);

// --- LÓGICA DOS RELÉS ---
#define RELE_ON LOW
#define RELE_OFF HIGH

// --- PARÂMETROS DE TEMPERATURA ---
#define TEMP_MAX_SEC 50.0
#define TEMP_ALVO_SEC 45.0
#define HISTERESE_SEC 1.0
#define TEMP_MAX_ARM 30.0
#define TEMP_MIN_ARM 15.0

// ================= ESTADO GLOBAL =================

float tempSensors[5] = {0,0,0,0,0};
float umidSensors[5] = {0,0,0,0,0};
float mediaT = 0; float mediaU = 0;
bool lampadaLigada = false; bool coolerLigado = false;
bool modoSecagem = false;
unsigned long ultimaLeitura = 0;

unsigned long ultimoSync = 0;
bool syncImediato = false;      // força sync fora do intervalo (botão físico)
bool origemBotao = false;       // marca que a última troca veio do botão

enum Estado { AQUECENDO, MANTENDO, RESFRIANDO, ESTAVEL, ERRO };
Estado estadoAtual = ESTAVEL;

void controlarClima();

const char* nomeEstado() {
  switch (estadoAtual) {
    case AQUECENDO:  return "AQUECENDO";
    case MANTENDO:   return "MANTENDO";
    case RESFRIANDO: return "RESFRIANDO";
    case ERRO:       return "ERRO";
    default:         return "ESTAVEL";
  }
}

// Adiciona um float ao JSON, ou null se o sensor falhou (NaN)
void jsonCampoFloat(String& json, const char* chave, float valor, int casas) {
  json += "\""; json += chave; json += "\":";
  if (isnan(valor)) json += "null";
  else json += String(valor, casas);
  json += ",";
}

// ==========================================
// SINCRONIZAÇÃO COM O SERVIDOR DO FABLAB
// ==========================================
void sincronizarComServidor() {
  if (WiFi.status() != WL_CONNECTED) return;

  // Monta o payload JSON
  String json;
  json.reserve(512);
  json = "{";
  json += "\"modo\":\""; json += (modoSecagem ? "SECAGEM" : "ARMAZEM"); json += "\",";
  json += "\"estado\":\""; json += nomeEstado(); json += "\",";
  jsonCampoFloat(json, "temperatura_media", (estadoAtual == ERRO ? NAN : mediaT), 1);
  jsonCampoFloat(json, "umidade_media", (estadoAtual == ERRO ? NAN : mediaU), 0);
  jsonCampoFloat(json, "t1", tempSensors[0], 1); jsonCampoFloat(json, "h1", umidSensors[0], 0);
  jsonCampoFloat(json, "t2", tempSensors[1], 1); jsonCampoFloat(json, "h2", umidSensors[1], 0);
  jsonCampoFloat(json, "t3", tempSensors[2], 1); jsonCampoFloat(json, "h3", umidSensors[2], 0);
  jsonCampoFloat(json, "t4", tempSensors[3], 1); jsonCampoFloat(json, "h4", umidSensors[3], 0);
  jsonCampoFloat(json, "t5", tempSensors[4], 1); jsonCampoFloat(json, "h5", umidSensors[4], 0);
  json += "\"lampada\":"; json += (lampadaLigada ? "true" : "false"); json += ",";
  json += "\"cooler\":"; json += (coolerLigado ? "true" : "false"); json += ",";
  json += "\"origem_botao\":"; json += (origemBotao ? "true" : "false");
  json += "}";

  HTTPClient http;
  http.setTimeout(10000);

  bool usaHttps = String(SERVER_URL).startsWith("https");
  WiFiClientSecure clientSecure;
  WiFiClient clientPlano;

  bool ok;
  if (usaHttps) {
    clientSecure.setInsecure(); // sem validação de CA (ESP32 sem certificados)
    ok = http.begin(clientSecure, SERVER_URL);
  } else {
    ok = http.begin(clientPlano, SERVER_URL);
  }
  if (!ok) { Serial.println("Falha ao iniciar conexao com o servidor"); return; }

  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-Estufa-Token", ESTUFA_TOKEN);

  int httpCode = http.POST(json);

  if (httpCode == 200) {
    String resposta = http.getString();
    origemBotao = false; // botão já foi reportado com sucesso

    // Resposta esperada: {"ok": true, "modo_desejado": "SECAGEM"|"ARMAZEM"}
    bool desejaSecagem = (resposta.indexOf("\"modo_desejado\": \"SECAGEM\"") >= 0) ||
                         (resposta.indexOf("\"modo_desejado\":\"SECAGEM\"") >= 0);
    bool desejaArmazem = (resposta.indexOf("\"modo_desejado\": \"ARMAZEM\"") >= 0) ||
                         (resposta.indexOf("\"modo_desejado\":\"ARMAZEM\"") >= 0);

    if (desejaSecagem && !modoSecagem) {
      modoSecagem = true;
      Serial.println("Servidor: mudou para SECAGEM");
      controlarClima();
    } else if (desejaArmazem && modoSecagem) {
      modoSecagem = false;
      Serial.println("Servidor: mudou para ARMAZENAMENTO");
      controlarClima();
    }
    Serial.println("Sync OK com o servidor do FabLab");
  } else {
    Serial.printf("Sync falhou: HTTP %d (%s)\n", httpCode,
                  http.errorToString(httpCode).c_str());
  }

  http.end();
  if (usaHttps) clientSecure.stop();
}

// ==========================================
// PÁGINA WEB LOCAL (acesso dentro do laboratório)
// ==========================================
void paginaPrincipal() {
  String html = "<!DOCTYPE html><html><head>";
  html += "<meta name='viewport' content='width=device-width, initial-scale=1.0'>";
  html += "<meta http-equiv='refresh' content='3'>";
  html += "<style>body{font-family:Arial,sans-serif; text-align:center; background-color:#222; color:#fff; margin-top:30px;}";
  html += "h1{color:#4CAF50;} .painel{background:#333; padding:20px; border-radius:10px; display:inline-block;}";
  html += ".erro{color:#ff4c4c;}</style></head><body>";

  html += "<h1>Painel da Estufa</h1>";
  html += "<div class='painel'>";

  if (estadoAtual == ERRO) {
    html += "<h2 class='erro'>ALERTA: FALHA NOS SENSORES!</h2>";
    html += "<p>Verifique as conexoes dos DHT22.</p>";
  } else {
    html += "<p>Modo Atual: <b>" + String(modoSecagem ? "SECAGEM (45&deg;C)" : "ARMAZEM") + "</b></p>";
    html += "<h2 style='font-size:40px; margin:10px 0;'>" + String(mediaT, 1) + " &deg;C</h2>";
    html += "<h3 style='color:#aaa;'>" + String(mediaU, 0) + " % Umidade</h3>";
    html += "<hr style='border:1px solid #555;'>";
    html += "<p>Lampada: <b>" + String(lampadaLigada ? "<span style='color:yellow'>ON</span>" : "OFF") + "</b> | ";
    html += "Cooler: <b>" + String(coolerLigado ? "<span style='color:cyan'>ON</span>" : "OFF") + "</b></p>";
  }

  html += "</div></body></html>";
  server.send(200, "text/html", html);
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.print("\nA ligar a rede ");
  Serial.println(ssid);
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWi-Fi Conectado!");
  Serial.print("IP do painel local: ");
  Serial.println(WiFi.localIP());

  ArduinoOTA.setHostname("Estufa-IoT");
  ArduinoOTA.begin();

  server.on("/", paginaPrincipal);
  server.begin();

  pinMode(LAMPADA_PIN, OUTPUT); pinMode(COOLER_PIN, OUTPUT);
  pinMode(BOTAO_SECAGEM, INPUT_PULLUP); pinMode(BOTAO_ARMAZEM, INPUT_PULLUP);
  digitalWrite(LAMPADA_PIN, RELE_OFF); digitalWrite(COOLER_PIN, RELE_OFF);

  dht1.begin(); dht2.begin(); dht3.begin(); dht4.begin(); dht5.begin();
  delay(2000);
}

void lerSensoresEFazerMedia() {
  float somaT = 0, somaU = 0; int sensoresValidos = 0;

  tempSensors[0] = dht1.readTemperature(); umidSensors[0] = dht1.readHumidity();
  tempSensors[1] = dht2.readTemperature(); umidSensors[1] = dht2.readHumidity();
  tempSensors[2] = dht3.readTemperature(); umidSensors[2] = dht3.readHumidity();
  tempSensors[3] = dht4.readTemperature(); umidSensors[3] = dht4.readHumidity();
  tempSensors[4] = dht5.readTemperature(); umidSensors[4] = dht5.readHumidity();

  for (int i = 0; i < 5; i++) {
    if (!isnan(tempSensors[i]) && !isnan(umidSensors[i])) {
      somaT += tempSensors[i]; somaU += umidSensors[i]; sensoresValidos++;
    }
  }

  if (sensoresValidos > 0) {
    mediaT = somaT / sensoresValidos;
    mediaU = somaU / sensoresValidos;
    if (estadoAtual == ERRO) estadoAtual = ESTAVEL; // sensores voltaram
    controlarClima();
  } else {
    estadoAtual = ERRO;
    digitalWrite(LAMPADA_PIN, RELE_OFF); digitalWrite(COOLER_PIN, RELE_OFF);
    lampadaLigada = false; coolerLigado = false;
  }
}

void controlarClima() {
  if (modoSecagem) {
    if (mediaT >= TEMP_MAX_SEC) { digitalWrite(LAMPADA_PIN, RELE_OFF); digitalWrite(COOLER_PIN, RELE_ON); lampadaLigada = false; coolerLigado = true; estadoAtual = RESFRIANDO; }
    else if (coolerLigado && mediaT < (TEMP_MAX_SEC - 2.0)) { digitalWrite(COOLER_PIN, RELE_OFF); coolerLigado = false; }
    else if (mediaT < (TEMP_ALVO_SEC - HISTERESE_SEC)) { digitalWrite(LAMPADA_PIN, RELE_ON); lampadaLigada = true; estadoAtual = AQUECENDO; }
    else if (mediaT > (TEMP_ALVO_SEC + HISTERESE_SEC) && mediaT < TEMP_MAX_SEC) { digitalWrite(LAMPADA_PIN, RELE_OFF); lampadaLigada = false; estadoAtual = MANTENDO; }
  } else {
    if (mediaT >= TEMP_MAX_ARM) { digitalWrite(LAMPADA_PIN, RELE_OFF); digitalWrite(COOLER_PIN, RELE_ON); lampadaLigada = false; coolerLigado = true; estadoAtual = RESFRIANDO; }
    else if (mediaT <= TEMP_MIN_ARM) { digitalWrite(LAMPADA_PIN, RELE_ON); digitalWrite(COOLER_PIN, RELE_OFF); lampadaLigada = true; coolerLigado = false; estadoAtual = AQUECENDO; }
    else { digitalWrite(LAMPADA_PIN, RELE_OFF); digitalWrite(COOLER_PIN, RELE_OFF); lampadaLigada = false; coolerLigado = false; estadoAtual = ESTAVEL; }
  }
  if (!lampadaLigada && !coolerLigado && estadoAtual != ERRO) estadoAtual = ESTAVEL;
}

void loop() {
  ArduinoOTA.handle();
  server.handleClient();

  // ===================================================
  // BOTÕES FÍSICOS (com sync imediato para o servidor)
  // ===================================================
  bool modoAnterior = modoSecagem;

  if (digitalRead(BOTAO_SECAGEM) == LOW) {
    delay(50); // Debounce
    if (digitalRead(BOTAO_SECAGEM) == LOW && !modoSecagem) {
      modoSecagem = true;
      origemBotao = true;
      syncImediato = true;
      Serial.println("Botao Fisico: Mudou para SECAGEM");
    }
  }

  if (digitalRead(BOTAO_ARMAZEM) == LOW) {
    delay(50); // Debounce
    if (digitalRead(BOTAO_ARMAZEM) == LOW && modoSecagem) {
      modoSecagem = false;
      origemBotao = true;
      syncImediato = true;
      Serial.println("Botao Fisico: Mudou para ARMAZENAMENTO");
    }
  }

  if (modoSecagem != modoAnterior) { controlarClima(); }

  // 1. Atualiza sensores locais (a cada 2.5s)
  if (millis() - ultimaLeitura >= 2500) {
    ultimaLeitura = millis();
    lerSensoresEFazerMedia();
  }

  // 2. Sincroniza com o servidor do FabLab (a cada 30s ou após botão)
  if (syncImediato || (millis() - ultimoSync >= SYNC_INTERVALO)) {
    syncImediato = false;
    ultimoSync = millis();
    sincronizarComServidor();
  }
}
