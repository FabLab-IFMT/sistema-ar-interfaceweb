#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <HardwareSerial.h>

// --- Configurações WiFi ---
const char* ssid = "Fabnet";
const char* password = "71037523";

// --- URLs do servidor Django ---
const char* serverUrl = "http://192.168.1.103:8000";  // Atualize com o IP do seu servidor Django
const char* verifyCardUrl = "/acesso_e_ponto/verificar_cartao/";
const char* checkReadingStatusUrl = "/users/cards/check-reading-status/";
const char* registerCardUrl = "/users/cards/register/";

// --- Pinos e configuração do sensor RFID ---
#define RFID_RX_PIN 16
#define RFID_TX_PIN 17
HardwareSerial RFID(2);  // Utilizando UART2 do ESP32

// --- Pino de controle da catraca ---
// Estado normal: catraca energizada (HIGH) (mecanismo travado)
#define ACCESS_PIN 12

// --- Pinos de indicação do modo de operação ---
#define NORMAL_MODE_LED 25   // LED verde - modo normal (controle de acesso)
#define REGISTER_MODE_LED 26 // LED azul - modo de registro de cartão

// --- Controle de leitura repetida ---
String lastCardProcessed = "";
unsigned long lastProcessedTime = 0;
const unsigned long processCooldown = 5000; // 5 segundos de cooldown

// --- Controle de modo ---
bool registrationMode = false;
unsigned long lastCheckTime = 0;
const unsigned long checkInterval = 2000; // 2 segundos entre verificações

void setup() {
  Serial.begin(115200);

  // Inicializa o sensor RFID
  RFID.begin(9600, SERIAL_8N1, RFID_RX_PIN, RFID_TX_PIN);

  // Configura o pino de controle da catraca como saída
  pinMode(ACCESS_PIN, OUTPUT);
  digitalWrite(ACCESS_PIN, HIGH);  // Estado normal: catraca energizada (travada)
  
  // Configura os LEDs indicadores de modo
  pinMode(NORMAL_MODE_LED, OUTPUT);
  pinMode(REGISTER_MODE_LED, OUTPUT);
  digitalWrite(NORMAL_MODE_LED, HIGH);  // Inicialmente no modo normal
  digitalWrite(REGISTER_MODE_LED, LOW);

  // Conecta ao WiFi
  Serial.print("Conectando ao WiFi...");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println(" Conectado!");
  Serial.print("IP do ESP32: ");
  Serial.println(WiFi.localIP());

  Serial.println("Aguardando leitura do sensor RFID (RDM6300)...");
}

void loop() {
  // Verifica se deve mudar o modo de operação
  unsigned long currentTime = millis();
  if (currentTime - lastCheckTime > checkInterval) {
    checkOperationMode();
    lastCheckTime = currentTime;
  }
  
  // Verifica se há dados disponíveis do sensor RFID
  if (RFID.available() > 0) {
    if (RFID.peek() == 0x02) {
      if (RFID.available() >= 14) {
        byte frame[14];
        for (int i = 0; i < 14; i++) {
          frame[i] = RFID.read();
        }
        if (frame[0] == 0x02 && frame[13] == 0x03) {
          char tagCode[11];  // 10 caracteres + '\0'
          memcpy(tagCode, frame + 1, 10);
          tagCode[10] = '\0';
          String cardCode = String(tagCode);
          Serial.print("Tag lida: ");
          Serial.println(cardCode);

          // Verifica se o mesmo cartão foi processado recentemente
          unsigned long currentTime = millis();
          if (cardCode == lastCardProcessed && (currentTime - lastProcessedTime) < processCooldown) {
            // Se estiver dentro do cooldown, ignora a leitura
            return;
          }
          lastCardProcessed = cardCode;
          lastProcessedTime = currentTime;
          
          // Decide o modo de processamento
          if (registrationMode) {
            registerCardToUser(cardCode);
          } else {
            // Modo normal: verificar se o cartão está autorizado
            if (isCardAuthorized(cardCode)) {
              grantAccess();
            } else {
              Serial.println("Acesso negado.");
            }
          }
        } else {
          Serial.println("Frame inválido.");
        }
      }
    } else {
      RFID.read(); // Descarte caso não seja o byte inicial esperado
    }
  }
}

// --- Função para verificar o modo de operação ---
void checkOperationMode() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(String(serverUrl) + String(checkReadingStatusUrl));
    
    int httpCode = http.GET();
    
    if (httpCode == HTTP_CODE_OK) {
      String response = http.getString();
      DynamicJsonDocument doc(1024);
      DeserializationError error = deserializeJson(doc, response);
      
      if (!error) {
        bool newMode = doc["reading_active"];
        
        // Se houver mudança de modo
        if (newMode != registrationMode) {
          registrationMode = newMode;
          
          if (registrationMode) {
            Serial.println("Alterando para modo de registro de cartão!");
            digitalWrite(NORMAL_MODE_LED, LOW);
            digitalWrite(REGISTER_MODE_LED, HIGH);
          } else {
            Serial.println("Alterando para modo normal de controle de acesso!");
            digitalWrite(NORMAL_MODE_LED, HIGH);
            digitalWrite(REGISTER_MODE_LED, LOW);
          }
        }
      }
    }
    http.end();
  }
}

// --- Função para registrar um cartão a um usuário ---
void registerCardToUser(const String &cardCode) {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(String(serverUrl) + String(registerCardUrl));
    http.addHeader("Content-Type", "application/json");
    
    DynamicJsonDocument doc(200);
    doc["card_number"] = cardCode;
    String requestBody;
    serializeJson(doc, requestBody);
    
    int httpCode = http.POST(requestBody);
    
    if (httpCode == HTTP_CODE_OK) {
      String response = http.getString();
      DynamicJsonDocument responseDoc(1024);
      DeserializationError error = deserializeJson(responseDoc, response);
      
      if (!error) {
        bool success = responseDoc["success"];
        String message = responseDoc["message"].as<String>();
        
        if (success) {
          String userName = responseDoc["user_name"].as<String>();
          Serial.print("Cartão registrado com sucesso para ");
          Serial.println(userName);
          
          // Piscar o LED de registro para indicar sucesso
          for (int i = 0; i < 5; i++) {
            digitalWrite(REGISTER_MODE_LED, LOW);
            delay(200);
            digitalWrite(REGISTER_MODE_LED, HIGH);
            delay(200);
          }
          
          // Após o registro bem-sucedido, voltar automaticamente para o modo normal
          registrationMode = false;
          digitalWrite(NORMAL_MODE_LED, HIGH);
          digitalWrite(REGISTER_MODE_LED, LOW);
        } else {
          Serial.print("Erro no registro do cartão: ");
          Serial.println(message);
        }
      }
    } else {
      Serial.printf("Erro HTTP: %d\n", httpCode);
    }
    http.end();
  }
}

// --- Função de verificação de autorização diretamente no Django ---
bool isCardAuthorized(const String &cardCode) {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(String(serverUrl) + String(verifyCardUrl));
    http.addHeader("Content-Type", "application/json");

    // Criando JSON para enviar ao servidor
    DynamicJsonDocument doc(200);
    doc["card_number"] = cardCode;
    String requestBody;
    serializeJson(doc, requestBody);

    int httpCode = http.POST(requestBody);

    if (httpCode == HTTP_CODE_OK) {
      String response = http.getString();
      DynamicJsonDocument responseDoc(1024);
      DeserializationError error = deserializeJson(responseDoc, response);

      if (!error) {
        bool authorized = responseDoc["authorized"];
        String message = responseDoc["message"].as<String>();
        Serial.print("Resposta do servidor: ");
        Serial.println(message);
        http.end();
        return authorized;
      } else {
        Serial.println("Erro ao interpretar JSON de resposta");
      }
    } else {
      Serial.printf("Erro HTTP: %d\n", httpCode);
      Serial.println(http.getString());
    }
    http.end();
  } else {
    Serial.println("Erro: WiFi não conectado");
  }
  return false;
}

// --- Função para liberar a catraca: desenergiza temporariamente o mecanismo ---
void grantAccess() {
  Serial.println("Acesso concedido! Desenergizando catraca.");
  digitalWrite(ACCESS_PIN, LOW);   // Desenergiza para liberar o mecanismo
  delay(3000);                     // Tempo para a passagem (3 segundos)
  digitalWrite(ACCESS_PIN, HIGH);  // Reenergiza, travando novamente a catraca
}
