using System.Text.Json;
using System.Text.Json.Serialization;

namespace AIAgentManagement.Infrastructure;

/// <summary>
/// Dictionary&lt;string, object&gt; 직렬화 시 값이 JsonElement인 경우(클라이언트에서 역직렬화된 경우) 올바르게 직렬화합니다.
/// </summary>
public class DictionaryStringObjectJsonConverter : JsonConverter<Dictionary<string, object>>
{
    public override Dictionary<string, object>? Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
    {
        return JsonSerializer.Deserialize<Dictionary<string, object>>(ref reader, options);
    }

    public override void Write(Utf8JsonWriter writer, Dictionary<string, object> value, JsonSerializerOptions options)
    {
        if (value == null)
        {
            writer.WriteNullValue();
            return;
        }
        writer.WriteStartObject();
        foreach (var kv in value)
        {
            if (string.IsNullOrEmpty(kv.Key))
                continue;
            string? rawJson = null;
            try
            {
                if (kv.Value is JsonElement je)
                    rawJson = je.GetRawText();
                else if (kv.Value == null)
                    rawJson = "null";
                else if (kv.Value is System.Text.Json.Nodes.JsonNode node)
                    rawJson = node.ToJsonString();
            }
            catch { }
            try
            {
                writer.WritePropertyName(kv.Key);
                if (rawJson != null)
                    writer.WriteRawValue(rawJson);
                else if (kv.Value == null)
                    writer.WriteNullValue();
                else
                    JsonSerializer.Serialize(writer, kv.Value, options);
            }
            catch
            {
                try { writer.WriteNullValue(); } catch { }
            }
        }
        writer.WriteEndObject();
    }
}
