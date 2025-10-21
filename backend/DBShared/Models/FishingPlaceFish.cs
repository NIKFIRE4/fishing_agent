using System.ComponentModel.DataAnnotations;

namespace DBShared.Models
{
    public class FishingPlaceFish
    {
        [Key]
        public int IdFishingPlace { get; set; }
        public Places? FishingPlace { get; set; }

        public int IdFishType { get; set; }
        public FishType? FishType { get; set; }
    }
}
