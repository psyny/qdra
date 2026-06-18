import React, { useState, useRef } from 'react';
import { validateImageFile } from '../utils/imageUtils';

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
  const [editingImage, setEditingImage] = useState<string | null>(null);
  const [imageDimensions, setImageDimensions] = useState({ width: 0, height: 0 });
  const [scale, setScale] = useState(1);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  
  const editorSize = targetSize * 1.5; // Editor is 1.5x the target size to show more context

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file type
    const validation = validateImageFile(file);
    if (!validation.valid) {
      onUploadError?.(validation.error || 'Invalid file');
      return;
    }

    // Load image for editing
    const reader = new FileReader();
    reader.onload = (e) => {
      const img = new Image();
      img.onload = () => {
        setImageDimensions({ width: img.width, height: img.height });
        setEditingImage(e.target?.result as string);
        
        // Calculate scale based on smallest dimension to fill the target square
        const minDimension = Math.min(img.width, img.height);
        const initialScale = targetSize / minDimension;
        setScale(initialScale);
        
        // Center the image with center-based transform origin
        // With transform-origin: center center, the visual center of the scaled image is at:
        // position.x + (img.width * scale) / 2, position.y + (img.height * scale) / 2
        // To center in editor: position.x + (img.width * scale) / 2 = editorSize / 2
        const initialX = editorSize / 2 - img.width / 2;
        const initialY = editorSize / 2 - img.height / 2;
        setPosition({ x: initialX, y: initialY });
      };
      img.src = e.target?.result as string;
    };
    reader.readAsDataURL(file);
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX - position.x, y: e.clientY - position.y });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging) return;
    setPosition({
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y,
    });
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const handleConfirmEdit = async () => {
    if (!editingImage || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Create a temporary image to get dimensions
    const img = new Image();
    img.onload = async () => {
      // Set canvas to target size
      canvas.width = targetSize;
      canvas.height = targetSize;
      
      // The crop area in editor coordinates (centered)
      const cropAreaLeft = (editorSize - targetSize) / 2;
      const cropAreaTop = (editorSize - targetSize) / 2;
      
      // Clear canvas
      ctx.fillStyle = '#000';
      ctx.fillRect(0, 0, targetSize, targetSize);
      
      // Draw the image
      // CSS: left: position.x, top: position.y, transform: scale(scale), transform-origin: center center
      // The transform-origin is at (img.width/2, img.height/2) relative to image top-left
      // After scaling, the visual center stays at (position.x + img.width/2, position.y + img.height/2) in parent coords
      
      ctx.save();
      // Translate for crop area offset (canvas 0,0 = cropAreaLeft, cropAreaTop in editor)
      ctx.translate(-cropAreaLeft, -cropAreaTop);
      // Translate to image position
      ctx.translate(position.x, position.y);
      // Move to center of image (transform origin)
      ctx.translate(img.width / 2, img.height / 2);
      // Scale
      ctx.scale(scale, scale);
      // Move back from center
      ctx.translate(-img.width / 2, -img.height / 2);
      // Draw image
      ctx.drawImage(img, 0, 0);
      ctx.restore();

      // Convert to blob
      canvas.toBlob(async (blob: Blob | null) => {
        if (!blob) return;
        
        setEditingImage(null);
        setPreviewUrl(URL.createObjectURL(blob));
        
        // Proceed with upload
        await uploadImage(blob);
      }, 'image/png');
    };
    img.src = editingImage;
  };

  const uploadImage = async (blob: Blob) => {
    setIsUploading(true);

    try {
      // Get dimensions from the blob
      const img = new Image();
      img.onload = async () => {
        const width = img.width;
        const height = img.height;

        // Request presigned upload URL
        const presignResponse = await fetch(`/api/entities/${entityId}/images/presign-upload`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            filename: 'image.png',
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
        setIsUploading(false);
      };
      img.src = URL.createObjectURL(blob);
    } catch (error) {
      console.error('Upload error:', error);
      onUploadError?.(error instanceof Error ? error.message : 'Upload failed');
      setPreviewUrl(currentImage || null);
      setIsUploading(false);
    } finally {
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
      
      {editingImage ? (
        <div className="image-editor">
          <div 
            className="image-editor-canvas"
            style={{ 
              width: editorSize, 
              height: editorSize, 
              border: '2px solid #ccc',
              position: 'relative',
              overflow: 'hidden',
              cursor: isDragging ? 'grabbing' : 'grab',
              margin: '0 auto',
            }}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp}
          >
            <img
              src={editingImage}
              alt="Editing"
              style={{
                position: 'absolute',
                left: position.x,
                top: position.y,
                transform: `scale(${scale})`,
                transformOrigin: 'center center',
                pointerEvents: 'none',
              }}
            />
            {/* Target square overlay */}
            <div
              style={{
                position: 'absolute',
                left: (editorSize - targetSize) / 2,
                top: (editorSize - targetSize) / 2,
                width: targetSize,
                height: targetSize,
                border: '3px solid rgba(255,255,255,0.8)',
                boxShadow: '0 0 0 9999px rgba(0,0,0,0.5)',
                pointerEvents: 'none',
              }}
            />
          </div>
          <div className="image-editor-controls mb-4" style={{ marginTop: '16px', display: 'flex', gap: '12px', alignItems: 'center' }}>
            <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <label style={{ fontSize: '14px', color: '#666' }}>Zoom:</label>
              <input
                type="range"
                min="0.1"
                max="5"
                step="0.1"
                value={scale}
                onChange={(e) => setScale(parseFloat(e.target.value))}
                style={{ flex: 1 }}
              />
              <span style={{ fontSize: '14px', minWidth: '50px', textAlign: 'right' }}>{Math.round(scale * 100)}%</span>
            </div>
          </div>
          <div className="form-actions" style={{ display: 'flex', gap: '12px' }}>
            <button 
              onClick={() => setEditingImage(null)} 
              disabled={isUploading} 
              type="button"
              className="button button--secondary"
            >
              Cancel
            </button>
            <button 
              onClick={handleConfirmEdit} 
              disabled={isUploading} 
              type="button"
              className="button button--primary"
            >
              {isUploading ? 'Uploading...' : 'Confirm & Upload'}
            </button>
          </div>
        </div>
      ) : (
        <>
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
        </>
      )}
      <canvas ref={canvasRef} style={{ display: 'none' }} />
    </div>
  );
}
