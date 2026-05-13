using System.ComponentModel.DataAnnotations;
using System.Text.Json.Serialization;

namespace AIAgentManagement.DTOs;

public class SendMessageRequestDto
{
    [Required]
    public string Message { get; set; } = string.Empty;

    public bool? Stream { get; set; }
    public bool? EnableWebSearch { get; set; }
    public bool? EnableRag { get; set; }
    public int? RagTopK { get; set; }
    public string? Language { get; set; } // 'ko', 'en', 'auto'

    /// <summary>
    /// H3(5-3) — 멀티모달 첨부(image_url 등). Frontend 가 업로드된 이미지/파일을 이 배열에 담아 전송하면
    /// ChatService 가 마지막 user 메시지의 Contents 로 결합하여 LLM 의 vision payload 로 전달한다.
    /// 비어 있거나 null 이면 텍스트 전용 메시지로 동작(기존 호환).
    /// </summary>
    [JsonPropertyName("attachments")]
    public List<MessageContentDto>? Attachments { get; set; }
}
