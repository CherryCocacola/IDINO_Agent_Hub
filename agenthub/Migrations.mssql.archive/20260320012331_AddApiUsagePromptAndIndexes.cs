using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace AIAgentManagement.Migrations
{
    /// <inheritdoc />
    public partial class AddApiUsagePromptAndIndexes : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            // ApiUsage.Prompt 컬럼 추가 (ChatMessages 별도 쿼리 제거용, 최대 500자)
            migrationBuilder.AddColumn<string>(
                name: "Prompt",
                table: "ApiUsages",
                type: "nvarchar(500)",
                maxLength: 500,
                nullable: true);

            // 날짜 범위 단독 필터 인덱스
            migrationBuilder.CreateIndex(
                name: "IX_ApiUsages_RequestTime",
                table: "ApiUsages",
                column: "RequestTime");

            // 서비스별 날짜 범위 필터 인덱스
            migrationBuilder.CreateIndex(
                name: "IX_ApiUsages_RequestTime_ServiceId",
                table: "ApiUsages",
                columns: new[] { "RequestTime", "ServiceId" });

            // 상태별 날짜 범위 필터 인덱스
            migrationBuilder.CreateIndex(
                name: "IX_ApiUsages_RequestTime_StatusCode",
                table: "ApiUsages",
                columns: new[] { "RequestTime", "StatusCode" });
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropIndex(
                name: "IX_ApiUsages_RequestTime_StatusCode",
                table: "ApiUsages");

            migrationBuilder.DropIndex(
                name: "IX_ApiUsages_RequestTime_ServiceId",
                table: "ApiUsages");

            migrationBuilder.DropIndex(
                name: "IX_ApiUsages_RequestTime",
                table: "ApiUsages");

            migrationBuilder.DropColumn(
                name: "Prompt",
                table: "ApiUsages");
        }
    }
}
