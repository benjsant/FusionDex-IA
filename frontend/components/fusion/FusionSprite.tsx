"use client";

// Fusion sprite = one 96x96 cell cropped from a spritesheet hosted by the
// Infinite Fusion project itself (same source the official game uses).
// Layout: 1920x2784 sheet, 20 columns × 29 rows of 96x96 cells.
// col = body_id % 20, row = body_id / 20  (see DownloadedSettings.rb & BaseSpriteExtracter.rb).

const SHEET_BASE =
  process.env.NEXT_PUBLIC_FUSION_SPRITES_URL ??
  "https://infinitefusion.net/customsprites/spritesheets/spritesheets_custom";

const COLS = 20;
const TILE = 96;

export interface FusionSpriteProps {
  headId: number;
  bodyId: number;
  size?: number;
  className?: string;
}

export function FusionSprite({
  headId,
  bodyId,
  size = 128,
  className = "",
}: FusionSpriteProps) {
  const col = bodyId % COLS;
  const row = Math.floor(bodyId / COLS);
  const scale = size / TILE;

  const style: React.CSSProperties = {
    width: size,
    height: size,
    backgroundImage: `url("${SHEET_BASE}/${headId}/${headId}.png")`,
    backgroundPosition: `-${col * size}px -${row * size}px`,
    backgroundSize: `${COLS * size}px auto`,
    backgroundRepeat: "no-repeat",
    imageRendering: "pixelated",
  };

  return (
    <div
      role="img"
      aria-label={`Fusion ${headId}/${bodyId}`}
      className={className}
      style={style}
    />
  );
}
