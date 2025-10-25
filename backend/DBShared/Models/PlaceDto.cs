using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.Linq;
using System.Text;
using System.Text.Json.Serialization;
using System.Threading.Tasks;

namespace DBShared.Models
{
    public class PlaceDto
    {       

        [JsonPropertyName("name_place")]
        public string? NamePlace { get; set; }

        [JsonPropertyName("type_of_relax")]
        public string? RelaxType { get; set; }

        [JsonPropertyName("user_preferences")]
        public List<string>? UserPreferences { get; set; }

        [JsonPropertyName("place_coordinates")]
        public List<decimal>? PlaceCoordinates { get; set; }

        [JsonPropertyName("description")]
        public string? Description { get; set; }

        [JsonPropertyName("caught_fishes")]
        public List<string>? CaughtFishes { get; set; }

        [JsonPropertyName("water_space")]
        public List<string>? WaterSpace { get; set; }
    }
}
