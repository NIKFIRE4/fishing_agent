using Microsoft.EntityFrameworkCore.Migrations;
using Npgsql.EntityFrameworkCore.PostgreSQL.Metadata;

#nullable disable

namespace DBShared.Migrations
{
    /// <inheritdoc />
    public partial class RenameColumns : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropForeignKey(
                name: "FK_FishingPlaceFish_FishingPlaces_IdFishingPlace",
                table: "FishingPlaceFish");

            migrationBuilder.DropForeignKey(
                name: "FK_FishingPlaceWater_FishingPlaces_IdFishingPlace",
                table: "FishingPlaceWater");

            migrationBuilder.DropForeignKey(
                name: "FK_TgMessages_FishingPlaces_PlaceId",
                table: "TgMessages");

            migrationBuilder.DropTable(
                name: "FishingPlaces");

            migrationBuilder.CreateTable(
                name: "Places",
                columns: table => new
                {
                    IdPlace = table.Column<int>(type: "integer", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    PlaceName = table.Column<string>(type: "text", nullable: true),
                    Latitude = table.Column<decimal>(type: "numeric", nullable: true),
                    Longitude = table.Column<decimal>(type: "numeric", nullable: true),
                    PlaceDescription = table.Column<string>(type: "text", nullable: true),
                    PlaceType = table.Column<string>(type: "text", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Places", x => x.IdPlace);
                });

            migrationBuilder.CreateIndex(
                name: "IX_Places_IdPlace",
                table: "Places",
                column: "IdPlace",
                unique: true);

            migrationBuilder.AddForeignKey(
                name: "FK_FishingPlaceFish_Places_IdFishingPlace",
                table: "FishingPlaceFish",
                column: "IdFishingPlace",
                principalTable: "Places",
                principalColumn: "IdPlace",
                onDelete: ReferentialAction.Cascade);

            migrationBuilder.AddForeignKey(
                name: "FK_FishingPlaceWater_Places_IdFishingPlace",
                table: "FishingPlaceWater",
                column: "IdFishingPlace",
                principalTable: "Places",
                principalColumn: "IdPlace",
                onDelete: ReferentialAction.Cascade);

            migrationBuilder.AddForeignKey(
                name: "FK_TgMessages_Places_PlaceId",
                table: "TgMessages",
                column: "PlaceId",
                principalTable: "Places",
                principalColumn: "IdPlace",
                onDelete: ReferentialAction.SetNull);
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropForeignKey(
                name: "FK_FishingPlaceFish_Places_IdFishingPlace",
                table: "FishingPlaceFish");

            migrationBuilder.DropForeignKey(
                name: "FK_FishingPlaceWater_Places_IdFishingPlace",
                table: "FishingPlaceWater");

            migrationBuilder.DropForeignKey(
                name: "FK_TgMessages_Places_PlaceId",
                table: "TgMessages");

            migrationBuilder.DropTable(
                name: "Places");

            migrationBuilder.CreateTable(
                name: "FishingPlaces",
                columns: table => new
                {
                    IdFishingPlace = table.Column<int>(type: "integer", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    Latitude = table.Column<decimal>(type: "numeric", nullable: true),
                    Longitude = table.Column<decimal>(type: "numeric", nullable: true),
                    PlaceDescription = table.Column<string>(type: "text", nullable: true),
                    PlaceName = table.Column<string>(type: "text", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_FishingPlaces", x => x.IdFishingPlace);
                });

            migrationBuilder.CreateIndex(
                name: "IX_FishingPlaces_IdFishingPlace",
                table: "FishingPlaces",
                column: "IdFishingPlace",
                unique: true);

            migrationBuilder.AddForeignKey(
                name: "FK_FishingPlaceFish_FishingPlaces_IdFishingPlace",
                table: "FishingPlaceFish",
                column: "IdFishingPlace",
                principalTable: "FishingPlaces",
                principalColumn: "IdFishingPlace",
                onDelete: ReferentialAction.Cascade);

            migrationBuilder.AddForeignKey(
                name: "FK_FishingPlaceWater_FishingPlaces_IdFishingPlace",
                table: "FishingPlaceWater",
                column: "IdFishingPlace",
                principalTable: "FishingPlaces",
                principalColumn: "IdFishingPlace",
                onDelete: ReferentialAction.Cascade);

            migrationBuilder.AddForeignKey(
                name: "FK_TgMessages_FishingPlaces_PlaceId",
                table: "TgMessages",
                column: "PlaceId",
                principalTable: "FishingPlaces",
                principalColumn: "IdFishingPlace",
                onDelete: ReferentialAction.SetNull);
        }
    }
}
