#include "settings_portal_service.h"

#include <algorithm>
#include <cmath>
#include <cstring>
#include <string>
#include <vector>

#include <cJSON.h>
#include <esp_log.h>
#include <nvs.h>

#include "api_balance_service.h"
#include "reporter_service.h"
#include "settings.h"

namespace {

constexpr char kTag[] = "PanelSettings";
constexpr size_t kMaximumBodyBytes = 4096;

const char kSettingsPage[] = R"HTML(<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Summon Syna-sama</title><style>
*{box-sizing:border-box}body{margin:0;background:#f1f1ef;color:#111;font-family:system-ui,"Microsoft YaHei",sans-serif}.card{max-width:620px;margin:20px auto;padding:24px;background:#fff;border:2px solid #111;border-radius:18px;box-shadow:6px 6px 0 #111}h1{font-size:25px;margin:0 0 7px}.sub,.tip{color:#555;line-height:1.55}.sub{margin:0 0 18px}.tip{font-size:13px;margin:7px 0 0}fieldset{margin:16px 0;padding:15px;border:2px solid #111;border-radius:12px}legend{padding:0 7px;font-weight:800}label{display:block;font-weight:700;margin:12px 0 6px}input,select,textarea{width:100%;padding:11px;border:2px solid #111;border-radius:8px;font-size:16px;background:#fff}textarea{min-height:76px;resize:vertical}button{width:100%;margin-top:15px;padding:13px;border:2px solid #111;border-radius:8px;background:#111;color:#fff;font-size:17px;font-weight:800}.notice{display:none;padding:11px;margin:0 0 14px;border:1px solid #111;border-radius:8px;background:#eee}.row{display:grid;grid-template-columns:1fr 1fr;gap:12px}@media(max-width:520px){.card{margin:0;border-radius:0;box-shadow:none}.row{grid-template-columns:1fr}}</style></head><body><main class="card"><h1>Summon Syna-sama</h1><p class="sub">Unified settings for network, Reporter, API balance, Syna voice, and battery calibration. Passwords and tokens are not echoed; leaving blank keeps existing values.</p><div id="notice" class="notice"></div><form id="form">
<fieldset><legend>Network and Time</legend><label>Wi-Fi / Mobile Hotspot Name</label><input name="ssid" list="networks" maxlength="32" autocomplete="off"><datalist id="networks"></datalist><label>Wi-Fi Password</label><input name="password" type="password" maxlength="64" autocomplete="new-password" placeholder="Leave blank to keep saved password"><p class="tip">If you are not changing the network, leave both blank. The device syncs time automatically when connected; timezone is fixed to China Standard Time UTC+8.</p></fieldset>
<fieldset><legend>Computer Reporter</legend><label>Pairing Token</label><input name="reporter_token" type="password" maxlength="96" autocomplete="off" placeholder="Leave blank to keep existing token"><p class="tip">Must match the token in the computer Reporter.</p></fieldset>
<fieldset><legend>API Balance</legend><label>Provider Display Name</label><input name="api_provider" maxlength="40" placeholder="DeepSeek / OpenRouter / self-hosted"><label>API Base URL</label><input name="api_base" maxlength="200" placeholder="https://api.example.com"><label>API Key</label><input name="api_key" type="password" maxlength="160" autocomplete="off" placeholder="Leave blank to keep existing key"><label>Balance Fetch Method</label><select name="balance_adapter"><option value="disabled">Do not query balance</option><option value="deepseek">DeepSeek official preset</option><option value="custom">Custom HTTP endpoint</option></select><section id="custom"><label>Balance Endpoint URL</label><input name="balance_url" maxlength="240"><div class="row"><div><label>Request Method</label><select name="balance_method"><option>GET</option><option>POST</option></select></div><div><label>Authentication</label><select name="balance_auth"><option value="bearer">Bearer</option><option value="header">Custom header</option><option value="query">URL parameter</option><option value="none">No auth</option></select></div></div><label>Header / Parameter Name</label><input name="balance_auth_name" maxlength="64" placeholder="Authorization"><label>Balance JSON Path</label><input name="balance_value_path" maxlength="160" placeholder="data.balance"><div class="row"><div><label>Fixed Unit</label><input name="balance_unit" maxlength="16" placeholder="CNY"></div><div><label>Numeric Scale</label><input name="balance_scale" type="number" step="0.000001"></div></div><label>Unit JSON Path (optional)</label><input name="balance_unit_path" maxlength="160"><label>POST JSON (optional)</label><textarea name="balance_body" maxlength="512" placeholder="Leave blank to keep existing content; you can use {{API_KEY}}"></textarea></section></fieldset>
<fieldset><legend>Syna Voice</legend><p class="tip">Current Xiaozhi cloud capability is managed by device activation info; no need to share the Key with the balance API.</p><label>OTA / Config Service URL (advanced, optional)</label><input name="ota_url" maxlength="240"><p class="tip">Leave blank to use the firmware's default official URL. An incorrect value can prevent obtaining Xiaozhi cloud config on next boot.</p></fieldset>
<fieldset><legend>Battery Calibration</legend><label>Voltage Scale</label><input name="battery_scale" type="number" min="2.5" max="3.5" step="0.001"><p class="tip">Default 3.000. New scale = current scale × multimeter measured voltage ÷ displayed voltage.</p></fieldset><button type="submit">Save Settings</button></form><p class="tip">To enter again later, hold BOOT, then long-press KEY for about 3 seconds. Saved Wi-Fi will not be deleted.</p></main><script>
const f=document.getElementById('form'),n=document.getElementById('notice'),custom=document.getElementById('custom');const show=m=>{n.textContent=m;n.style.display='block';scrollTo(0,0)};const sync=()=>custom.style.display=f.balance_adapter.value==='custom'?'block':'none';f.balance_adapter.onchange=sync;
fetch('/panel/config').then(r=>r.json()).then(c=>{for(const[k,v]of Object.entries(c)){if(f.elements[k]&&v!==null)f.elements[k].value=v}sync()}).catch(()=>show('Failed to load settings; please refresh the page'));
fetch('/scan').then(r=>r.json()).then(x=>{const d=document.getElementById('networks');for(const a of(x.aps||[])){const o=document.createElement('option');o.value=String(a.ssid);d.appendChild(o)}}).catch(()=>{});
f.onsubmit=async e=>{e.preventDefault();const o=Object.fromEntries(new FormData(f));show('Saving…');try{let r=await fetch('/panel/save',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(o)}),j=await r.json();if(!j.success)throw Error(j.error||'Save failed');if(o.ssid){r=await fetch('/submit',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ssid:o.ssid,password:o.password})});j=await r.json();if(!j.success)throw Error(j.error||'Wi-Fi connection failed')}else{r=await fetch('/exit',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});j=await r.json();if(!j.success)throw Error(j.error||'Failed to exit settings mode')}show('Settings saved. Device is reconnecting; Syna-0721 will close automatically.')}catch(x){show(x.message)}};sync();
</script></body></html>)HTML";

void AddString(cJSON* root, const char* name, const std::string& value) {
    cJSON_AddStringToObject(root, name, value.c_str());
}

bool ReadFloat(const char* ns, const char* key, float& value) {
    nvs_handle_t handle = 0;
    if (nvs_open(ns, NVS_READONLY, &handle) != ESP_OK) return false;
    size_t size = sizeof(value);
    const esp_err_t result = nvs_get_blob(handle, key, &value, &size);
    nvs_close(handle);
    return result == ESP_OK;
}

void WriteFloat(const char* ns, const char* key, float value) {
    nvs_handle_t handle = 0;
    if (nvs_open(ns, NVS_READWRITE, &handle) != ESP_OK) return;
    if (nvs_set_blob(handle, key, &value, sizeof(value)) == ESP_OK) nvs_commit(handle);
    nvs_close(handle);
}

void SetIfPresent(Settings& settings, const cJSON* root, const char* json_name,
                  const char* key, bool allow_empty = true) {
    const cJSON* item = cJSON_GetObjectItemCaseSensitive(root, json_name);
    if (!cJSON_IsString(item) || item->valuestring == nullptr) return;
    if (allow_empty || item->valuestring[0] != '\0') settings.SetString(key, item->valuestring);
}

}  // namespace

SettingsPortalService& SettingsPortalService::GetInstance() {
    static SettingsPortalService instance;
    return instance;
}

esp_err_t SettingsPortalService::ServeRoot(httpd_req_t* request) {
    httpd_resp_set_type(request, "text/html; charset=utf-8");
    httpd_resp_set_hdr(request, "Cache-Control", "no-store");
    httpd_resp_set_hdr(request, "Connection", "close");
    return httpd_resp_send(request, kSettingsPage, HTTPD_RESP_USE_STRLEN);
}

void SettingsPortalService::RegisterHandlers(httpd_handle_t server) {
    const httpd_uri_t config = {
        .uri = "/panel/config", .method = HTTP_GET,
        .handler = HandleConfig, .user_ctx = this};
    const httpd_uri_t save = {
        .uri = "/panel/save", .method = HTTP_POST,
        .handler = HandleSave, .user_ctx = this};
    ESP_ERROR_CHECK(httpd_register_uri_handler(server, &config));
    ESP_ERROR_CHECK(httpd_register_uri_handler(server, &save));
}

float SettingsPortalService::GetBatteryScale() {
    const int cached = battery_scale_milli_.load();
    if (cached != 0) return cached / 1000.0f;
    float scale = 3.0f;
    if (!ReadFloat("wifi-config", "bat-scale", scale) || !std::isfinite(scale) ||
        scale < 2.5f || scale > 3.5f) scale = 3.0f;
    battery_scale_milli_.store(static_cast<int>(std::lround(scale * 1000.0f)));
    return scale;
}

esp_err_t SettingsPortalService::HandleConfig(httpd_req_t* request) {
    Settings panel("wifi-config");
    Settings wifi("wifi");
    cJSON* root = cJSON_CreateObject();
    AddString(root, "api_provider", panel.GetString("api-provider", "API"));
    AddString(root, "api_base", panel.GetString("api-base", ""));
    AddString(root, "balance_adapter", panel.GetString("bal-adapter", "disabled"));
    AddString(root, "balance_url", panel.GetString("bal-url", ""));
    AddString(root, "balance_method", panel.GetString("bal-method", "GET"));
    AddString(root, "balance_auth", panel.GetString("bal-auth", "bearer"));
    AddString(root, "balance_auth_name", panel.GetString("bal-hname", "Authorization"));
    AddString(root, "balance_value_path", panel.GetString("bal-path", "data.balance"));
    AddString(root, "balance_unit", panel.GetString("bal-unit", ""));
    AddString(root, "balance_unit_path", panel.GetString("bal-upath", ""));
    cJSON_AddNumberToObject(root, "balance_scale", [&]() { float v = 1.0f; ReadFloat("wifi-config", "bal-scale", v); return v; }());
    cJSON_AddNumberToObject(root, "battery_scale", SettingsPortalService::GetInstance().GetBatteryScale());
    AddString(root, "ota_url", wifi.GetString("ota_url", ""));
    char* json = cJSON_PrintUnformatted(root);
    cJSON_Delete(root);
    httpd_resp_set_type(request, "application/json");
    httpd_resp_set_hdr(request, "Cache-Control", "no-store");
    const esp_err_t result = httpd_resp_send(request, json, HTTPD_RESP_USE_STRLEN);
    cJSON_free(json);
    return result;
}

esp_err_t SettingsPortalService::HandleSave(httpd_req_t* request) {
    if (request->content_len == 0 || request->content_len > kMaximumBodyBytes) {
        httpd_resp_send_err(request, HTTPD_400_BAD_REQUEST, "Invalid payload size");
        return ESP_FAIL;
    }
    std::vector<char> body(request->content_len + 1);
    size_t received = 0;
    while (received < request->content_len) {
        const int count = httpd_req_recv(request, body.data() + received,
                                         request->content_len - received);
        if (count <= 0) {
            httpd_resp_send_err(request, HTTPD_400_BAD_REQUEST, "Failed to receive payload");
            return ESP_FAIL;
        }
        received += count;
    }
    body[received] = '\0';
    cJSON* root = cJSON_Parse(body.data());
    if (root == nullptr) {
        httpd_resp_send_err(request, HTTPD_400_BAD_REQUEST, "Invalid JSON");
        return ESP_FAIL;
    }
    {
        Settings panel("wifi-config", true);
        SetIfPresent(panel, root, "reporter_token", "reporter", false);
        SetIfPresent(panel, root, "api_provider", "api-provider");
        SetIfPresent(panel, root, "api_base", "api-base");
        SetIfPresent(panel, root, "api_key", "api-key", false);
        SetIfPresent(panel, root, "balance_adapter", "bal-adapter");
        SetIfPresent(panel, root, "balance_url", "bal-url");
        SetIfPresent(panel, root, "balance_method", "bal-method");
        SetIfPresent(panel, root, "balance_auth", "bal-auth");
        SetIfPresent(panel, root, "balance_auth_name", "bal-hname");
        SetIfPresent(panel, root, "balance_value_path", "bal-path");
        SetIfPresent(panel, root, "balance_unit", "bal-unit");
        SetIfPresent(panel, root, "balance_unit_path", "bal-upath");
        SetIfPresent(panel, root, "balance_body", "bal-body", false);
    }
    {
        Settings wifi("wifi", true);
        SetIfPresent(wifi, root, "ota_url", "ota_url");
    }
    const cJSON* balance_scale = cJSON_GetObjectItemCaseSensitive(root, "balance_scale");
    if (cJSON_IsString(balance_scale) && balance_scale->valuestring) {
        const float value = strtof(balance_scale->valuestring, nullptr);
        if (std::isfinite(value) && value != 0 && std::fabs(value) <= 1000000) {
            WriteFloat("wifi-config", "bal-scale", value);
        }
    }
    const cJSON* battery_scale = cJSON_GetObjectItemCaseSensitive(root, "battery_scale");
    if (cJSON_IsString(battery_scale) && battery_scale->valuestring) {
        const float value = strtof(battery_scale->valuestring, nullptr);
        if (std::isfinite(value) && value >= 2.5f && value <= 3.5f) {
            WriteFloat("wifi-config", "bat-scale", value);
            SettingsPortalService::GetInstance().battery_scale_milli_.store(
                static_cast<int>(std::lround(value * 1000.0f)));
        }
    }
    cJSON_Delete(root);
    ReporterService::GetInstance().RequestReload();
    ApiBalanceService::GetInstance().RequestRefresh();
    ESP_LOGI(kTag, "Settings saved; secret values were not echoed");
    httpd_resp_set_type(request, "application/json");
    return httpd_resp_sendstr(request, "{\"success\":true}");
}

extern "C" esp_err_t wifi_config_custom_root(httpd_req_t* request) {
    return SettingsPortalService::GetInstance().ServeRoot(request);
}

extern "C" void wifi_config_register_custom_handlers(httpd_handle_t server) {
    SettingsPortalService::GetInstance().RegisterHandlers(server);
}

extern "C" const char* wifi_config_custom_ssid() {
    return "Syna-0721";
}
