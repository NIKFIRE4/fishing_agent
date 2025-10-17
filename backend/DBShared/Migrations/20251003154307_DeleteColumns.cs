using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace DBShared.Migrations
{
    /// <inheritdoc />
    public partial class DeleteColumns : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropForeignKey(
                name: "FK_FishingPlaceWater_FishingPlaces_IdWaterType",
                table: "FishingPlaceWater");

            migrationBuilder.DropColumn(
                name: "CaughtFishes",
                table: "FishingPlaces");

            migrationBuilder.DropColumn(
                name: "WaterPlace",
                table: "FishingPlaces");

            migrationBuilder.AddForeignKey(
                name: "FK_FishingPlaceWater_FishingPlaces_IdFishingPlace",
                table: "FishingPlaceWater",
                column: "IdFishingPlace",
                principalTable: "FishingPlaces",
                principalColumn: "IdFishingPlace",
                onDelete: ReferentialAction.Cascade);
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropForeignKey(
                name: "FK_FishingPlaceWater_FishingPlaces_IdFishingPlace",
                table: "FishingPlaceWater");

            migrationBuilder.AddColumn<string>(
                name: "CaughtFishes",
                table: "FishingPlaces",
                type: "text",
                nullable: true);

            migrationBuilder.AddColumn<string>(
                name: "WaterPlace",
                table: "FishingPlaces",
                type: "text",
                nullable: true);

            migrationBuilder.AddForeignKey(
                name: "FK_FishingPlaceWater_FishingPlaces_IdWaterType",
                table: "FishingPlaceWater",
                column: "IdWaterType",
                principalTable: "FishingPlaces",
                principalColumn: "IdFishingPlace",
                onDelete: ReferentialAction.Cascade);
        }
    }
}
