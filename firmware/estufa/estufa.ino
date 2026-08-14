/*
 * ============================================================
 * ESTUFA DE FILAMENTO - INTEGRADA AO SERVIDOR DO FABLAB (v2)
 * ============================================================
 * Comunicação com o servidor Django (a estufa sempre inicia,
 * pois está atrás do NAT do laboratório):
 *
 *   - GET  /estufa/api/comandos/   a cada ~2,5 s (poll leve):
 *     recebe modo desejado, controle AUTO/MANUAL, estado desejado
 *     da lâmpada/ventoinha e os parâmetros de temperatura.
 *   - POST /estufa/api/telemetria/ a cada 30 s (ou após botão):
 *     envia leituras dos 5 DHT22 e estado atual.
 *
 * Controle:
 *   - AUTO: termostato local com os parâmetros vindos do site.
 *   - MANUAL: obedece lâmpada/ventoinha definidos no site.
 *   - TRAVA DE SEGURANÇA (sempre ativa, mesmo em manual):
 *     media >= TEMP_SEGURANCA -> lâmpada OFF + ventoinha ON.
 *   - Sem contato com o servidor por mais de FALHA_COMANDOS_MS:
 *     volta sozinho para AUTO (fail-safe).
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
const char* URL_TELEMETRIA = "https://ifmaker.cba.ifmt.edu.br/estufa/api/telemetria/";
const char* URL_COMANDOS   = "https://ifmaker.cba.ifmt.edu.br/estufa/api/comandos/";
const char* ESTUFA_TOKEN   = "COLE_O_TOKEN_AQUI";

// Intervalos
const unsigned long COMANDOS_INTERVALO   = 2500;   // poll de comandos (~2,5 s)
const unsigned long TELEMETRIA_INTERVALO = 30000;  // envio de leituras (30 s)
const unsigned long FALHA_COMANDOS_MS    = 120000; // 2 min sem servidor -> volta pra AUTO

// Trava de segurança absoluta (não configurável pelo site de propósito)
#define TEMP_SEGURANCA 55.0

// ================= HARDWARE =================

WebServer server(80);

#define LAMPADA_PIN 5
#define COOLER_PIN 6
#define BOTAO_SECAGEM 2
#define BOTAO_ARMAZEM 3

#define DHTTYPE DHT22
DHT dht1(0, DHTTYPE); DHT dht2(1, DHTTYPE); DHT dht3(4, DHTTYPE); DHT dht4(7, DHTTYPE); DHT dht5(10, DHTTYPE);

#define RELE_ON LOW
#define RELE_OFF HIGH

// ================= PARÂMETROS (padrões; o servidor sobrescreve) =================

float tempAlvoSec  = 45.0;
float tempMaxSec   = 50.0;
float histereseSec = 1.0;
float tempMaxArm   = 30.0;
float tempMinArm   = 15.0;

// ================= ESTADO GLOBAL =================

float tempSensors[5] = {0,0,0,0,0};
float umidSensors[5] = {0,0,0,0,0};
float mediaT = 0; float mediaU = 0;
bool lampadaLigada = false; bool coolerLigado = false;
bool modoSecagem = false;

// Controle manual (definido pelo servidor)
bool controleManual = false;
bool lampadaDesejada = false;
bool coolerDesejado = false;

unsigned long ultimaLeitura = 0;
unsigned long ultimoComandos = 0;
unsigned long ultimaTelemetria = 0;
unsigned long ultimoContatoOk = 0;
bool syncImediato = false;
bool origemBotao = false;

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

// ================= HELPERS DE REDE =================

// Cliente TLS estático com reuso de conexão (evita handshake a cada poll)
WiFiClientSecure clientSecure;
HTTPClient http;

bool iniciarRequisicao(const char* url) {
  http.setTimeout(8000);
  http.setReuse(true); // keep-alive: a conexão sobrevive entre os polls
  if (!http.begin(clientSecure, url)) {
    Serial.println("Falha ao iniciar conexao");
    return false;
  }
  http.addHeader("X-Estufa-Token", ESTUFA_TOKEN);
  return true;
}

// --- Parsers simples para o JSON do servidor (sem ArduinoJson) ---
float pegarFloat(const String& s, const char* chave, float padrao) {
  String k = "\""; k += chave; k += "\":";
  int i = s.indexOf(k);
  if (i < 0) return padrao;
  i += k.length();
  while (i < (int)s.length() && s[i] == ' ') i++;
  return s.substring(i).toFloat();
}

bool pegarBool(const String& s, const char* chave, bool padrao) {
  String k = "\""; k += chave; k += "\":";
  int i = s.indexOf(k);
  if (i < 0) return padrao;
  i += k.length();
  while (i < (int)s.length() && s[i] == ' ') i++;
  return s.startsWith("true", i);
}

bool pegarModoSecagem(const String& s, bool padrao) {
  if (s.indexOf("\"modo_desejado\": \"SECAGEM\"") >= 0 ||
      s.indexOf("\"modo_desejado\":\"SECAGEM\"") >= 0) return true;
  if (s.indexOf("\"modo_desejado\": \"ARMAZEM\"") >= 0 ||
      s.indexOf("\"modo_desejado\":\"ARMAZEM\"") >= 0) return false;
  return padrao;
}

// Aplica a resposta do servidor (mesma estrutura nos dois endpoints)
void aplicarComandos(const String& resposta) {
  bool novoModoSecagem = pegarModoSecagem(resposta, modoSecagem);
  bool novoManual = (resposta.indexOf("\"controle\": \"MANUAL\"") >= 0 ||
                     resposta.indexOf("\"controle\":\"MANUAL\"") >= 0);

  lampadaDesejada = pegarBool(resposta, "lampada_desejada", lampadaDesejada);
  coolerDesejado  = pegarBool(resposta, "cooler_desejado", coolerDesejado);

  tempAlvoSec  = pegarFloat(resposta, "temp_alvo_sec", tempAlvoSec);
  tempMaxSec   = pegarFloat(resposta, "temp_max_sec", tempMaxSec);
  histereseSec = pegarFloat(resposta, "histerese_sec", histereseSec);
  tempMaxArm   = pegarFloat(resposta, "temp_max_arm", tempMaxArm);
  tempMinArm   = pegarFloat(resposta, "temp_min_arm", tempMinArm);

  bool mudou = (novoModoSecagem != modoSecagem) || (novoManual != controleManual);
  if (novoModoSecagem != modoSecagem) {
    modoSecagem = novoModoSecagem;
    Serial.println(modoSecagem ? "Servidor: SECAGEM" : "Servidor: ARMAZENAMENTO");
  }
  if (novoManual != controleManual) {
    controleManual = novoManual;
    Serial.println(controleManual ? "Servidor: controle MANUAL" : "Servidor: controle AUTO");
  }

  ultimoContatoOk = millis();
  if (mudou || controleManual) controlarClima();
}

// ================= POLL DE COMANDOS (leve, ~2,5 s) =================

void buscarComandos() {
  if (WiFi.status() != WL_CONNECTED) return;
  if (!iniciarRequisicao(URL_COMANDOS)) return;

  int httpCode = http.GET();
  if (httpCode == 200) {
    aplicarComandos(http.getString());
  } else {
    Serial.printf("Poll comandos falhou: HTTP %d\n", httpCode);
  }
  http.end();
}

// ================= TELEMETRIA (30 s) =================

void jsonCampoFloat(String& json, const char* chave, float valor, int casas) {
  json += "\""; json += chave; json += "\":";
  if (isnan(valor)) json += "null";
  else json += String(valor, casas);
  json += ",";
}

void enviarTelemetria() {
  if (WiFi.status() != WL_CONNECTED) return;

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

  if (!iniciarRequisicao(URL_TELEMETRIA)) return;
  http.addHeader("Content-Type", "application/json");

  int httpCode = http.POST(json);
  if (httpCode == 200) {
    aplicarComandos(http.getString());
    origemBotao = false;
    Serial.println("Telemetria OK");
  } else {
    Serial.printf("Telemetria falhou: HTTP %d (%s)\n", httpCode,
                  http.errorToString(httpCode).c_str());
  }
  http.end();
}

// ================= PÁGINA WEB LOCAL =================

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
    html += "<p>Modo: <b>" + String(modoSecagem ? "SECAGEM" : "ARMAZEM") + "</b>";
    html += " | Controle: <b>" + String(controleManual ? "MANUAL" : "AUTO") + "</b></p>";
    html += "<h2 style='font-size:40px; margin:10px 0;'>" + String(mediaT, 1) + " &deg;C</h2>";
    html += "<h3 style='color:#aaa;'>" + String(mediaU, 0) + " % Umidade</h3>";
    html += "<hr style='border:1px solid #555;'>";
    html += "<p>Lampada: <b>" + String(lampadaLigada ? "<span style='color:yellow'>ON</span>" : "OFF") + "</b> | ";
    html += "Cooler: <b>" + String(coolerLigado ? "<span style='color:cyan'>ON</span>" : "OFF") + "</b></p>";
  }

  html += "</div></body></html>";
  server.send(200, "text/html", html);
}

// ================= SETUP =================

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

  clientSecure.setInsecure(); // ESP32 sem bundle de certificados

  ArduinoOTA.setHostname("Estufa-IoT");
  ArduinoOTA.begin();

  server.on("/", paginaPrincipal);
  server.begin();

  pinMode(LAMPADA_PIN, OUTPUT); pinMode(COOLER_PIN, OUTPUT);
  pinMode(BOTAO_SECAGEM, INPUT_PULLUP); pinMode(BOTAO_ARMAZEM, INPUT_PULLUP);
  digitalWrite(LAMPADA_PIN, RELE_OFF); digitalWrite(COOLER_PIN, RELE_OFF);

  dht1.begin(); dht2.begin(); dht3.begin(); dht4.begin(); dht5.begin();
  delay(2000);

  ultimoContatoOk = millis();
}

// ================= SENSORES =================

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
    if (estadoAtual == ERRO) estadoAtual = ESTAVEL;
    controlarClima();
  } else {
    estadoAtual = ERRO;
    digitalWrite(LAMPADA_PIN, RELE_OFF); digitalWrite(COOLER_PIN, RELE_OFF);
    lampadaLigada = false; coolerLigado = false;
  }
}

// ================= CONTROLE =================

void setLampada(bool ligar) {
  digitalWrite(LAMPADA_PIN, ligar ? RELE_ON : RELE_OFF);
  lampadaLigada = ligar;
}

void setCooler(bool ligar) {
  digitalWrite(COOLER_PIN, ligar ? RELE_ON : RELE_OFF);
  coolerLigado = ligar;
}

void controlarClima() {
  if (estadoAtual == ERRO) return;

  // TRAVA DE SEGURANÇA — vale em qualquer modo, inclusive manual
  if (mediaT >= TEMP_SEGURANCA) {
    setLampada(false); setCooler(true);
    estadoAtual = RESFRIANDO;
    return;
  }

  // Controle manual: obedece o que veio do servidor
  if (controleManual) {
    setLampada(lampadaDesejada);
    setCooler(coolerDesejado);
    if (lampadaLigada && !coolerLigado)      estadoAtual = AQUECENDO;
    else if (coolerLigado && !lampadaLigada) estadoAtual = RESFRIANDO;
    else if (lampadaLigada && coolerLigado)  estadoAtual = MANTENDO;
    else                                     estadoAtual = ESTAVEL;
    return;
  }

  // Controle automático (termostato)
  if (modoSecagem) {
    if (mediaT >= tempMaxSec) { setLampada(false); setCooler(true); estadoAtual = RESFRIANDO; }
    else if (coolerLigado && mediaT < (tempMaxSec - 2.0)) { setCooler(false); }
    else if (mediaT < (tempAlvoSec - histereseSec)) { setLampada(true); estadoAtual = AQUECENDO; }
    else if (mediaT > (tempAlvoSec + histereseSec) && mediaT < tempMaxSec) { setLampada(false); estadoAtual = MANTENDO; }
  } else {
    if (mediaT >= tempMaxArm) { setLampada(false); setCooler(true); estadoAtual = RESFRIANDO; }
    else if (mediaT <= tempMinArm) { setLampada(true); setCooler(false); estadoAtual = AQUECENDO; }
    else { setLampada(false); setCooler(false); estadoAtual = ESTAVEL; }
  }
  if (!lampadaLigada && !coolerLigado) estadoAtual = ESTAVEL;
}

// ================= LOOP =================

void loop() {
  ArduinoOTA.handle();
  server.handleClient();

  // Botões físicos (mudam o modo; o servidor adota via origem_botao)
  bool modoAnterior = modoSecagem;

  if (digitalRead(BOTAO_SECAGEM) == LOW) {
    delay(50);
    if (digitalRead(BOTAO_SECAGEM) == LOW && !modoSecagem) {
      modoSecagem = true;
      origemBotao = true;
      syncImediato = true;
      Serial.println("Botao Fisico: SECAGEM");
    }
  }

  if (digitalRead(BOTAO_ARMAZEM) == LOW) {
    delay(50);
    if (digitalRead(BOTAO_ARMAZEM) == LOW && modoSecagem) {
      modoSecagem = false;
      origemBotao = true;
      syncImediato = true;
      Serial.println("Botao Fisico: ARMAZENAMENTO");
    }
  }

  if (modoSecagem != modoAnterior) { controlarClima(); }

  // Fail-safe: sem contato com o servidor há muito tempo -> volta pra AUTO
  if (controleManual && (millis() - ultimoContatoOk >= FALHA_COMANDOS_MS)) {
    controleManual = false;
    Serial.println("Sem contato com o servidor: voltando para controle AUTO");
    controlarClima();
  }

  // 1. Sensores locais (2,5 s)
  if (millis() - ultimaLeitura >= 2500) {
    ultimaLeitura = millis();
    lerSensoresEFazerMedia();
  }

  // 2. Poll de comandos do servidor (~2,5 s)
  if (millis() - ultimoComandos >= COMANDOS_INTERVALO) {
    ultimoComandos = millis();
    buscarComandos();
  }

  // 3. Telemetria completa (30 s ou após botão)
  if (syncImediato || (millis() - ultimaTelemetria >= TELEMETRIA_INTERVALO)) {
    syncImediato = false;
    ultimaTelemetria = millis();
    enviarTelemetria();
  }
}
