using System.Text.Json;
using System.Text.Json.Serialization;

namespace AIAgentManagement.Infrastructure;

/// <summary>
/// JsonElement를 raw JSON으로 직렬화합니다. Dictionary/List 내부의 JsonElement 값 직렬화 시 사용됩니다.
/// </summary>
public class JsonElementRawConverter : JsonConverter<JsonElement>
{
    public override JsonElement Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
    {
        using var doc = JsonDocument.ParseValue(ref reader);
        return doc.RootElement.Clone();
    }

    public override void Write(Utf8JsonWriter writer, JsonElement value, JsonSerializerOptions options)
    {
        value.WriteTo(writer);
    }
}
