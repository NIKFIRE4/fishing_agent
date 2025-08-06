using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace TgParse.Migrations
{
    /// <inheritdoc />
    public partial class SecondCrete : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.RenameColumn(
                name: "channelUrl",
                table: "TgMessages",
                newName: "СhannelUrl");

            migrationBuilder.CreateIndex(
                name: "IX_TgMessages_MessageId",
                table: "TgMessages",
                column: "MessageId",
                unique: true);
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropIndex(
                name: "IX_TgMessages_MessageId",
                table: "TgMessages");

            migrationBuilder.RenameColumn(
                name: "СhannelUrl",
                table: "TgMessages",
                newName: "channelUrl");
        }
    }
}
