using Microsoft.EntityFrameworkCore.Migrations;
using Npgsql.EntityFrameworkCore.PostgreSQL.Metadata;

#nullable disable

namespace DBShared.Migrations
{
    /// <inheritdoc />
    public partial class AddFishingPlacesTable : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.AddColumn<int>(
                name: "PlaceId",
                table: "TgMessages",
                type: "integer",
                nullable: true);

            migrationBuilder.CreateTable(
                name: "FishingPlaces",
                columns: table => new
                {
                    Id = table.Column<int>(type: "integer", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    Name = table.Column<string>(type: "text", nullable: true),
                    Latitude = table.Column<decimal>(type: "numeric", nullable: true),
                    Longitude = table.Column<decimal>(type: "numeric", nullable: true),
                    CaughtFishes = table.Column<string>(type: "text", nullable: true),
                    WaterPlace = table.Column<string>(type: "text", nullable: true),
                    PlaceDescription = table.Column<string>(type: "text", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_FishingPlaces", x => x.Id);
                });

            migrationBuilder.CreateTable(
                name: "FishType",
                columns: table => new
                {
                    Id = table.Column<int>(type: "integer", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    Name = table.Column<string>(type: "text", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_FishType", x => x.Id);
                });

            migrationBuilder.CreateTable(
                name: "WaterType",
                columns: table => new
                {
                    Id = table.Column<int>(type: "integer", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    Name = table.Column<string>(type: "text", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_WaterType", x => x.Id);
                });

            migrationBuilder.CreateTable(
                name: "FishingPlaceFish",
                columns: table => new
                {
                    FishingPlaceId = table.Column<int>(type: "integer", nullable: false),
                    FishTypeId = table.Column<int>(type: "integer", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_FishingPlaceFish", x => new { x.FishingPlaceId, x.FishTypeId });
                    table.ForeignKey(
                        name: "FK_FishingPlaceFish_FishType_FishTypeId",
                        column: x => x.FishTypeId,
                        principalTable: "FishType",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_FishingPlaceFish_FishingPlaces_FishingPlaceId",
                        column: x => x.FishingPlaceId,
                        principalTable: "FishingPlaces",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "FishingPlaceWater",
                columns: table => new
                {
                    FishingPlaceId = table.Column<int>(type: "integer", nullable: false),
                    WaterTypeId = table.Column<int>(type: "integer", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_FishingPlaceWater", x => new { x.FishingPlaceId, x.WaterTypeId });
                    table.ForeignKey(
                        name: "FK_FishingPlaceWater_FishingPlaces_WaterTypeId",
                        column: x => x.WaterTypeId,
                        principalTable: "FishingPlaces",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_FishingPlaceWater_WaterType_WaterTypeId",
                        column: x => x.WaterTypeId,
                        principalTable: "WaterType",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateIndex(
                name: "IX_TgMessages_PlaceId",
                table: "TgMessages",
                column: "PlaceId");

            migrationBuilder.CreateIndex(
                name: "IX_FishingPlaceFish_FishTypeId",
                table: "FishingPlaceFish",
                column: "FishTypeId");

            migrationBuilder.CreateIndex(
                name: "IX_FishingPlaces_Id",
                table: "FishingPlaces",
                column: "Id",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_FishingPlaceWater_WaterTypeId",
                table: "FishingPlaceWater",
                column: "WaterTypeId");

            migrationBuilder.AddForeignKey(
                name: "FK_TgMessages_FishingPlaces_PlaceId",
                table: "TgMessages",
                column: "PlaceId",
                principalTable: "FishingPlaces",
                principalColumn: "Id",
                onDelete: ReferentialAction.SetNull);
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropForeignKey(
                name: "FK_TgMessages_FishingPlaces_PlaceId",
                table: "TgMessages");

            migrationBuilder.DropTable(
                name: "FishingPlaceFish");

            migrationBuilder.DropTable(
                name: "FishingPlaceWater");

            migrationBuilder.DropTable(
                name: "FishType");

            migrationBuilder.DropTable(
                name: "FishingPlaces");

            migrationBuilder.DropTable(
                name: "WaterType");

            migrationBuilder.DropIndex(
                name: "IX_TgMessages_PlaceId",
                table: "TgMessages");

            migrationBuilder.DropColumn(
                name: "PlaceId",
                table: "TgMessages");
        }
    }
}
