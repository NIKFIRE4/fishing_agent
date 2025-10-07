using System.ComponentModel.DataAnnotations;

namespace TgParse.Models
{
    public class FishingPlaceWater
    {
        [Key]
        public int IdFishingPlace { get; set; }
        public FishingPlaces? FishingPlaces { get; set; }

        public int IdWaterType { get; set; }
        public WaterType? WaterType { get; set; }
    }
}
