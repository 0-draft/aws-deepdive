import fs from "node:fs";
import path from "node:path";

// Astro is always invoked from the web/ directory, so the repo root is one
// level up. We tried import.meta.url first, but Astro's bundler relocates the
// compiled module and the relative path no longer resolves to the source tree.
// cwd works as long as the invocation contract is honored — assert it so a
// wrong-cwd invocation fails loudly instead of silently rendering empty pages.
const ROOT = path.resolve(process.cwd(), "..");
if (!fs.existsSync(path.join(ROOT, "tracks"))) {
  throw new Error(
    `[awsdd-web] ROOT=${ROOT} does not contain a 'tracks/' directory. ` +
      `Astro commands must be run from the web/ directory (cwd). ` +
      `If you are invoking from elsewhere, cd into web/ first or use npm run --prefix web ...`,
  );
}

export const TRACKS = ["iam", "security", "whats-new", "releases"] as const;
export type Track = (typeof TRACKS)[number];

export interface Item {
  id: string;
  track: Track;
  source: string;
  source_kind: "rss" | "github" | string;
  url: string;
  title: string;
  summary: string;
  published_at: string;
  fetched_at: string;
  tags: string[];
  severity: string | null;
  score: number;
  score_breakdown: Record<string, number>;
}

export interface Report {
  track: Track;
  mode: "daily" | "weekly";
  slug: string;
  markdown: string;
  path: string;
}

export function tracks(): readonly Track[] {
  return TRACKS;
}

export function loadScored(track: Track): Item[] {
  const p = path.join(ROOT, "tracks", track, "data", "scored.json");
  if (!fs.existsSync(p)) return [];
  try {
    return JSON.parse(fs.readFileSync(p, "utf-8")) as Item[];
  } catch {
    return [];
  }
}

export function loadAll(): Item[] {
  return TRACKS.flatMap(loadScored);
}

export function loadReports(track: Track, mode: "daily" | "weekly"): Report[] {
  const dir = path.join(ROOT, "tracks", track, "reports", mode);
  if (!fs.existsSync(dir)) return [];
  return fs
    .readdirSync(dir)
    .filter((f) => f.endsWith(".md"))
    .sort()
    .reverse()
    .map((f) => ({
      track,
      mode,
      slug: f.replace(/\.md$/, ""),
      markdown: fs.readFileSync(path.join(dir, f), "utf-8"),
      path: path.join(dir, f),
    }));
}

const MS_IN_DAY = 86_400_000;

function isoWeekKey(d: Date): string | null {
  if (Number.isNaN(d.valueOf())) return null;
  const tmp = new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate()));
  const dayNum = tmp.getUTCDay() || 7;
  tmp.setUTCDate(tmp.getUTCDate() + 4 - dayNum);
  const yearStart = Date.UTC(tmp.getUTCFullYear(), 0, 1);
  const week = Math.ceil(((tmp.valueOf() - yearStart) / MS_IN_DAY + 1) / 7);
  return `${tmp.getUTCFullYear()}-W${String(week).padStart(2, "0")}`;
}

export interface WeekBucket {
  week: string;
  count: number;
}

export function weeklyVolume(items: Item[]): WeekBucket[] {
  const map = new Map<string, number>();
  for (const it of items) {
    const key = isoWeekKey(new Date(it.published_at));
    if (!key) continue;
    map.set(key, (map.get(key) ?? 0) + 1);
  }
  return [...map.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([week, count]) => ({ week, count }));
}
