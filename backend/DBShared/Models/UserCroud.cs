using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.Linq;
using System.Numerics;
using System.Text;
using System.Threading.Tasks;

namespace DBShared.Models
{
    public class UserCroud
    {
        [Key]
        public int Id { get; set; }

        [Required]
        public long UserId { get; set; }

        public string? Username { get; set; }

        public string? FirstName { get; set; }

        public string? LastName { get; set; }

        public DateTime RegistrationDate { get; set; } = DateTime.UtcNow;

        public int PostsCount { get; set; } = 0;

        public int SubmittedPostsCount { get; set; } = 0;

        public DateTime LastActivity { get; set; } = DateTime.UtcNow;


    }
}
