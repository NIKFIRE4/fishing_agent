using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace DBShared.Migrations
{
    /// <inheritdoc />
    public partial class IsProcessedForTgMessages : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.AddColumn<bool>(
                name: "IsProcessed",
                table: "TgMessages",
                type: "boolean",
                nullable: false,
                defaultValue: false);
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropColumn(
                name: "IsProcessed",
                table: "TgMessages");
        }
    }
}
