import React, { useState, useRef } from 'react';
import { resizeImageToSquare, validateImageFile } from '../utils/imageUtils';

interface ImageUploadProps {
  entityId: string;
  targetSize: number;
  onUploadComplete?: (imageUrl: string) => void;
  onUploadError?: (error: string) => void;
  onRemove?: () => void;
  currentImage?: string | null;
  currentImageId?: string | null;
}

export function ImageUpload({
  entityId,
  targetSize,
  onUploadComplete,
  onUploadError,
  onRemove,
  currentImage,
}: ImageUploadProps) {
  const [isUploading, setIsUploading] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(currentImage || null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file type
    const validation = validateImageFile(file);
    if (!validation.valid) {
      onUploadError?.(validation.error || 'Invalid file');
      return;
    }

    setIsUploading(true);

    try {
      // Resize image to square
      const { blob, width, height } = await resizeImageToSquare(file, targetSize);

      // Create preview
      const preview = URL.createObjectURL(blob);
      setPreviewUrl(preview);

      // Request presigned upload URL
      const presignResponse = await fetch(`/api/entities/${entityId}/images/presign-upload`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          filename: file.name,
          mime_type: blob.type,
          file_size_bytes: blob.size,
          width,
          height,
        }),
      });

      if (!presignResponse.ok) {
        throw new Error('Failed to get presigned upload URL');
      }

      const presignData = await presignResponse.json();

      // Upload to storage
      const uploadResponse = await fetch(presignData.upload_url, {
        method: 'PUT',
        headers: { 'Content-Type': blob.type },
        body: blob,
      });

      if (!uploadResponse.ok) {
        throw new Error('Failed to upload image');
      }

      // Finalize upload
      const finalizeResponse = await fetch(`/api/image-assets/${presignData.image_asset_id}/finalize`, {
        method: 'POST',
      });

      if (!finalizeResponse.ok) {
        throw new Error('Failed to finalize upload');
      }

      const finalizeData = await finalizeResponse.json();
      onUploadComplete?.(finalizeData.url);
    } catch (error) {
      console.error('Upload error:', error);
      onUploadError?.(error instanceof Error ? error.message : 'Upload failed');
      setPreviewUrl(currentImage || null);
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleRemove = async () => {
    if (!currentImage) return;
    
    try {
      // Delete the image via API
      const response = await fetch(`/api/entities/${entityId}/images`, {
        method: 'DELETE',
      });
      
      if (!response.ok) {
        throw new Error('Failed to remove image');
      }
      
      setPreviewUrl(null);
      onUploadComplete?.('');
      onRemove?.();
    } catch (error) {
      console.error('Remove error:', error);
      onUploadError?.(error instanceof Error ? error.message : 'Failed to remove image');
    }
  };

  return (
    <div className="image-upload">
      <div className="image-info mb-4" style={{ fontSize: '14px', color: '#666' }}>
        Target size: {targetSize}x{targetSize}px (square)
      </div>
      <div className="image-preview">
        {previewUrl ? (
          <img src={previewUrl} alt="Preview" style={{ width: targetSize, height: targetSize, objectFit: 'cover' }} />
        ) : (
          <div style={{ width: targetSize, height: targetSize, border: '2px dashed #ccc', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <span>No image</span>
          </div>
        )}
      </div>
      <div className="image-controls">
        <input
          ref={fileInputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          onChange={handleFileSelect}
          disabled={isUploading}
          style={{ display: 'none' }}
        />
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={isUploading}
          type="button"
        >
          {isUploading ? 'Uploading...' : 'Select Image'}
        </button>
        {previewUrl && (
          <button onClick={handleRemove} disabled={isUploading} type="button">
            Remove
          </button>
        )}
      </div>
    </div>
  );
}
