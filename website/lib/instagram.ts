// Recent posts, newest first. Add the code from the post's URL
// (instagram.com/reel/CODE/ or instagram.com/p/CODE/) and, if you like, what the job was.
export type Post = { code: string; kind: "reel" | "p"; car?: string; service?: string; suburb?: string };

// Pulled from @imperiumdetailing_ and each one opened to confirm it loads.
// A car or service is only set where the caption actually said so — the top two
// reels are captioned "DM us CERAMIC" and "😬😬😬", so they run without a label
// rather than carry a guess. No caption names a suburb, so none is set.
export const posts: Post[] = [
  { code: "Dcn6xptPICV", kind: "reel" },
  { code: "DcgQsoKPaX0", kind: "reel" },
  { code: "DcXqRumP51s", kind: "reel", car: "Ford Raptor", service: "Maintenance wash" },
  { code: "DapWgJpDxbp", kind: "p", car: "Audi RS5", service: "Full detail" },
  // Pat confirmed this one: the film was already on the car and we coated over
  // it. That is the distinction the site draws — we do not fit PPF, we will
  // coat film someone else fitted. See the coating FAQ in lib/services.ts.
  { code: "DZCId30D0CY", kind: "p", car: "Ferrari GTC4Lusso", service: "Ceramic coating over PPF and full detail" },
  { code: "DY_wU84j9Rs", kind: "p", car: "Porsche 911 GT3", service: "Exterior detail" },
  { code: "DYyp09BPZik", kind: "reel", car: "BMW M3" },
  { code: "DYl7UpwD92X", kind: "p", car: "BMW M3 CS and M3 Competition", service: "Exterior detail" },
];

// One line per recent job for the strip. Real cars, real work; add a line after each job.
export const recentJobs: { car: string; service: string; suburb?: string }[] = [
  { car: "BMW M4 Competition", service: "Full detail" },
  { car: "Ford Raptor", service: "Two-step correction and coating" },
  { car: "McLaren 650S", service: "Interior detail" },
  { car: "Lamborghini Huracán", service: "Exterior detail" },
  { car: "Nissan Patrol", service: "Paint correction" },
];

export const postUrl = (p: Post) => `https://www.instagram.com/${p.kind}/${p.code}/`;
