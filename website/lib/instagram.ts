// Recent posts, newest first. Add the code from the post's URL
// (instagram.com/reel/CODE/ or instagram.com/p/CODE/) and, if you like, what the job was.
export type Post = { code: string; kind: "reel" | "p"; car?: string; service?: string; suburb?: string };

export const posts: Post[] = [{ code: "DYyp09BPZik", kind: "reel" }];

// One line per recent job for the strip. Real cars, real work; add a line after each job.
export const recentJobs: { car: string; service: string; suburb?: string }[] = [
  { car: "BMW M4 Competition", service: "Full detail" },
  { car: "Ford Raptor", service: "Two-step correction and coating" },
  { car: "McLaren 650S", service: "Interior detail" },
  { car: "Lamborghini Huracán", service: "Exterior detail" },
  { car: "Nissan Patrol", service: "Paint correction" },
];

export const postUrl = (p: Post) => `https://www.instagram.com/${p.kind}/${p.code}/`;
