using System.ComponentModel.DataAnnotations;

namespace DBShared.Models
{
    public class WaterType
    {
        [Key]
        public int IdWaterType{ get; set; }
        public string? WaterName { get; set; }
        public List<FishingPlaceWater> FishingPlaceWaters { get; set; } = new List<FishingPlaceWater>();
    }
}
