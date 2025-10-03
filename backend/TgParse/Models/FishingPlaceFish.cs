using System.ComponentModel.DataAnnotations;

namespace TgParse.Models
{
    public class FishingPlaceFish
    {
        [Key]
        public int IdFishingPlace { get; set; }
        public FishingPlaces? FishingPlace { get; set; }

        public int IdFishType { get; set; }
        public FishType? FishType { get; set; }
    }
}
