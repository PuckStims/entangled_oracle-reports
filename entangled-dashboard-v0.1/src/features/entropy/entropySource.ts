export class CursorExhausted extends Error {}

export class HashCursor {
  private position = 0;

  constructor(private readonly hash: string) {
    validateAndNormalizeHash(hash);
  }

  get pos() {
    return this.position;
  }

  read(nibbles: number): number {
    if (this.position + nibbles > this.hash.length) {
      throw new CursorExhausted("Hash cursor exhausted.");
    }
    const slice = this.hash.slice(this.position, this.position + nibbles);
    this.position += nibbles;
    return Number.parseInt(slice, 16);
  }

  slice(start: number, nibbles: number): string {
    return this.hash.slice(start, start + nibbles);
  }
}

export function validateAndNormalizeHash(input: string): string {
  const normalized = input.trim().toLowerCase();
  if (!/^[0-9a-f]{64}$/.test(normalized)) {
    throw new Error("Invalid entropy hash.");
  }
  return normalized;
}

export async function sha256Hex(input: string): Promise<string> {
  const bytes = new TextEncoder().encode(input);
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
}

export async function deriveModalityHash(entropyHash: string, modality: string, version = "v1"): Promise<string> {
  return sha256Hex(`${validateAndNormalizeHash(entropyHash)}:${modality}:${version}`);
}

export async function generateEntropyHash(label = "dashboard-lock"): Promise<string> {
  const randomBytes = new Uint8Array(64);
  crypto.getRandomValues(randomBytes);
  const randomHex = [...randomBytes].map((byte) => byte.toString(16).padStart(2, "0")).join("");
  const timing = `${Date.now()}:${performance.now()}:${navigator.userAgent}:${label}`;
  return sha256Hex(`${randomHex}:${timing}`);
}
