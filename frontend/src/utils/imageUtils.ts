/**
 * Resize an image to a square of the specified size.
 * Returns a Promise that resolves to the resized image as a Blob.
 */
export async function resizeImageToSquare(
  file: File,
  targetSize: number,
  quality: number = 0.9
): Promise<{ blob: Blob; width: number; height: number }> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');

    if (!ctx) {
      reject(new Error('Failed to get canvas context'));
      return;
    }

    img.onload = () => {
      // Set canvas to target size (square)
      canvas.width = targetSize;
      canvas.height = targetSize;

      // Calculate scaling to cover the square
      const scale = Math.max(targetSize / img.width, targetSize / img.height);
      const scaledWidth = img.width * scale;
      const scaledHeight = img.height * scale;

      // Center the image
      const offsetX = (targetSize - scaledWidth) / 2;
      const offsetY = (targetSize - scaledHeight) / 2;

      // Draw the image (centered and scaled to cover)
      ctx.drawImage(img, offsetX, offsetY, scaledWidth, scaledHeight);

      // Convert to blob
      canvas.toBlob(
        (blob) => {
          if (blob) {
            resolve({ blob, width: targetSize, height: targetSize });
          } else {
            reject(new Error('Failed to convert canvas to blob'));
          }
        },
        file.type,
        quality
      );
    };

    img.onerror = () => {
      reject(new Error('Failed to load image'));
    };

    // Load the image
    const reader = new FileReader();
    reader.onload = (e) => {
      img.src = e.target?.result as string;
    };
    reader.onerror = () => {
      reject(new Error('Failed to read file'));
    };
    reader.readAsDataURL(file);
  });
}

/**
 * Get image dimensions without loading the full image.
 */
export function getImageDimensions(file: File): Promise<{ width: number; height: number }> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => {
      resolve({ width: img.width, height: img.height });
    };
    img.onerror = () => {
      reject(new Error('Failed to load image'));
    };
    const reader = new FileReader();
    reader.onload = (e) => {
      img.src = e.target?.result as string;
    };
    reader.onerror = () => {
      reject(new Error('Failed to read file'));
    };
    reader.readAsDataURL(file);
  });
}

/**
 * Validate that a file is an image and get its MIME type.
 */
export function validateImageFile(file: File): { valid: boolean; mimeType?: string; error?: string } {
  const allowedTypes = ['image/jpeg', 'image/png', 'image/webp'];
  
  if (!file.type.startsWith('image/')) {
    return { valid: false, error: 'File must be an image' };
  }
  
  if (!allowedTypes.includes(file.type)) {
    return { valid: false, error: 'Only JPEG, PNG, and WebP images are allowed' };
  }
  
  return { valid: true, mimeType: file.type };
}
