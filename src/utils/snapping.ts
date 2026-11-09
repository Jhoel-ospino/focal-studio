import { FocalElement, Guideline, SnapGridSize } from '../types/designer';

export interface SnapResult {
  x: number;
  y: number;
  guidelines: Guideline[];
}

export function calculateMagneticSnap(
  currentX: number,
  currentY: number,
  currentW: number,
  currentH: number,
  otherElements: FocalElement[],
  snapGrid: SnapGridSize,
  canvasWidth: number = 480,
  canvasHeight: number = 320,
  threshold: number = 6
): SnapResult {
  let snappedX = currentX;
  let snappedY = currentY;
  const guidelines: Guideline[] = [];

  // 1. Grid snapping baseline
  if (snapGrid > 0) {
    snappedX = Math.round(snappedX / snapGrid) * snapGrid;
    snappedY = Math.round(snappedY / snapGrid) * snapGrid;
  }

  // Current element reference points
  const left = currentX;
  const centerX = currentX + currentW / 2;
  const right = currentX + currentW;

  const top = currentY;
  const centerY = currentY + currentH / 2;
  const bottom = currentY + currentH;

  // Key canvas snap targets: edges (0, canvasWidth) and center (canvasWidth / 2)
  const targetXPoints = [0, canvasWidth / 2, canvasWidth];
  const targetYPoints = [0, canvasHeight / 2, canvasHeight];

  // Also collect bounding points from other elements
  for (const el of otherElements) {
    targetXPoints.push(el.x);
    targetXPoints.push(el.x + el.w / 2);
    targetXPoints.push(el.x + el.w);

    targetYPoints.push(el.y);
    targetYPoints.push(el.y + el.h / 2);
    targetYPoints.push(el.y + el.h);
  }

  // Find closest snap on X axis
  let minDiffX = threshold;
  let bestSnapX: number | null = null;
  let guideX: number | null = null;

  for (const tx of targetXPoints) {
    // Left edge align
    if (Math.abs(left - tx) < minDiffX) {
      minDiffX = Math.abs(left - tx);
      bestSnapX = tx;
      guideX = tx;
    }
    // Center align
    if (Math.abs(centerX - tx) < minDiffX) {
      minDiffX = Math.abs(centerX - tx);
      bestSnapX = tx - currentW / 2;
      guideX = tx;
    }
    // Right edge align
    if (Math.abs(right - tx) < minDiffX) {
      minDiffX = Math.abs(right - tx);
      bestSnapX = tx - currentW;
      guideX = tx;
    }
  }

  if (bestSnapX !== null && guideX !== null) {
    snappedX = bestSnapX;
    guidelines.push({ type: 'x', position: guideX });
  }

  // Find closest snap on Y axis
  let minDiffY = threshold;
  let bestSnapY: number | null = null;
  let guideY: number | null = null;

  for (const ty of targetYPoints) {
    // Top edge align
    if (Math.abs(top - ty) < minDiffY) {
      minDiffY = Math.abs(top - ty);
      bestSnapY = ty;
      guideY = ty;
    }
    // Center align
    if (Math.abs(centerY - ty) < minDiffY) {
      minDiffY = Math.abs(centerY - ty);
      bestSnapY = ty - currentH / 2;
      guideY = ty;
    }
    // Bottom edge align
    if (Math.abs(bottom - ty) < minDiffY) {
      minDiffY = Math.abs(bottom - ty);
      bestSnapY = ty - currentH;
      guideY = ty;
    }
  }

  if (bestSnapY !== null && guideY !== null) {
    snappedY = bestSnapY;
    guidelines.push({ type: 'y', position: guideY });
  }

  // Clamp within bounds (allow 0 to canvasWidth - w)
  snappedX = Math.max(0, Math.min(canvasWidth - currentW, snappedX));
  snappedY = Math.max(0, Math.min(canvasHeight - currentH, snappedY));

  return {
    x: snappedX,
    y: snappedY,
    guidelines
  };
}
