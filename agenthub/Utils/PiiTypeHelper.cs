namespace AIAgentManagement.Utils;

/// <summary>
/// PII 타입 이름 변환을 위한 유틸리티 클래스
/// </summary>
public static class PiiTypeHelper
{
    /// <summary>
    /// PII 타입 코드를 한글 이름으로 변환
    /// </summary>
    /// <param name="type">PII 타입 코드 (예: "PhoneNumber", "ResidentNumber")</param>
    /// <returns>한글 이름 (예: "휴대폰 번호", "주민등록번호")</returns>
    public static string GetPiiTypeName(string type)
    {
        return type switch
        {
            "PhoneNumber" => "휴대폰 번호",
            "ResidentNumber" => "주민등록번호",
            "CreditCard" => "신용카드 번호",
            "Email" => "이메일 주소",
            "AccountNumber" => "계좌번호",
            "DriverLicense" => "운전면허번호",
            "PassportNumber" => "여권번호",
            "AlienRegistrationNumber" => "외국인등록번호",
            _ => type
        };
    }

    /// <summary>
    /// 모든 지원되는 PII 타입 목록 반환
    /// </summary>
    /// <returns>PII 타입 코드 목록</returns>
    public static List<string> GetAllPiiTypes()
    {
        return new List<string>
        {
            "PhoneNumber",
            "ResidentNumber",
            "CreditCard",
            "Email",
            "AccountNumber",
            "DriverLicense",
            "PassportNumber",
            "AlienRegistrationNumber"
        };
    }
}
