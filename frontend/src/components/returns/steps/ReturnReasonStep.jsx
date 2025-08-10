import React, { useState } from 'react';
import { MessageSquare, Camera, Upload, AlertCircle, X } from 'lucide-react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../ui/select';
import { Textarea } from '../../ui/textarea';
import { Button } from '../../ui/button';
import { Alert, AlertDescription } from '../../ui/alert';

const ReturnReasonStep = ({ 
  formData, 
  updateFormData, 
  errors, 
  isLoading, 
  role 
}) => {
  const [uploadingPhotos, setUploadingPhotos] = useState({});

  const returnReasons = [
    { value: 'wrong_size', label: 'Wrong Size', requiresPhotos: false },
    { value: 'wrong_color', label: 'Wrong Color', requiresPhotos: false },
    { value: 'damaged_defective', label: 'Damaged/Defective', requiresPhotos: true },
    { value: 'not_as_described', label: 'Not as Described', requiresPhotos: false },
    { value: 'changed_mind', label: 'Changed Mind', requiresPhotos: false },
    { value: 'late_delivery', label: 'Late Delivery', requiresPhotos: false },
    { value: 'received_extra', label: 'Received Extra Item', requiresPhotos: false },
    { value: 'other', label: 'Other', requiresPhotos: false }
  ];

  const handleReasonChange = (itemId, field, value) => {
    const currentReasons = formData.itemReasons || {};
    const itemReason = currentReasons[itemId] || {};
    
    const updatedReasons = {
      ...currentReasons,
      [itemId]: {
        ...itemReason,
        [field]: value
      }
    };
    
    updateFormData({ itemReasons: updatedReasons });
  };

  const handlePhotoUpload = async (itemId, files) => {
    if (!files || files.length === 0) return;

    setUploadingPhotos(prev => ({ ...prev, [itemId]: true }));

    try {
      const formData = new FormData();
      Array.from(files).forEach(file => {
        formData.append('files', file);
      });

      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/unified-returns/upload-photos`, {
        method: 'POST',
        headers: {
          'X-Tenant-Id': localStorage.getItem('currentTenant') || 'tenant-fashion-store'
        },
        body: formData
      });

      const result = await response.json();
      
      if (result.success) {
        const currentReasons = formData.itemReasons || {};
        const itemReason = currentReasons[itemId] || {};
        const existingPhotos = itemReason.photos || [];
        
        const updatedReasons = {
          ...currentReasons,
          [itemId]: {
            ...itemReason,
            photos: [...existingPhotos, ...result.uploaded_files]
          }
        };
        
        updateFormData({ itemReasons: updatedReasons });
      }
    } catch (error) {
      console.error('Photo upload failed:', error);
    } finally {
      setUploadingPhotos(prev => ({ ...prev, [itemId]: false }));
    }
  };

  const removePhoto = (itemId, photoUrl) => {
    const currentReasons = formData.itemReasons || {};
    const itemReason = currentReasons[itemId] || {};
    const photos = itemReason.photos || [];
    
    const updatedReasons = {
      ...currentReasons,
      [itemId]: {
        ...itemReason,
        photos: photos.filter(photo => photo !== photoUrl)
      }
    };
    
    updateFormData({ itemReasons: updatedReasons });
  };

  const getReasonLabel = (value) => {
    const reason = returnReasons.find(r => r.value === value);
    return reason ? reason.label : value;
  };

  const requiresPhotos = (reason) => {
    const reasonObj = returnReasons.find(r => r.value === reason);
    return reasonObj ? reasonObj.requiresPhotos : false;
  };

  return (
    <div className="space-y-6">
      <div className="text-center">
        <MessageSquare className="h-12 w-12 text-blue-600 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          Reason for Return
        </h3>
        <p className="text-gray-600">
          Please provide the reason for returning each selected item
        </p>
      </div>

      <div className="space-y-6">
        {formData.selectedItems.map((item) => {
          const itemId = item.id || item.fulfillment_line_item_id;
          const itemReason = formData.itemReasons?.[itemId] || {};
          const reasonValue = itemReason.reason;
          const photos = itemReason.photos || [];
          
          return (
            <div key={itemId} className="border rounded-lg p-6 space-y-4">
              {/* Item Header */}
              <div className="flex items-start space-x-4">
                {item.image_url ? (
                  <img
                    src={item.image_url}
                    alt={item.title}
                    className="w-12 h-12 object-cover rounded-lg"
                  />
                ) : (
                  <div className="w-12 h-12 bg-gray-200 rounded-lg flex items-center justify-center">
                    <Camera className="h-5 w-5 text-gray-400" />
                  </div>
                )}
                <div className="flex-1">
                  <h4 className="font-medium text-gray-900">{item.title}</h4>
                  {item.variant_title && (
                    <p className="text-sm text-gray-600">{item.variant_title}</p>
                  )}
                  <p className="text-sm text-gray-500">Quantity: {item.quantity}</p>
                </div>
              </div>

              {/* Reason Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Return Reason *
                </label>
                <Select
                  value={reasonValue || ''}
                  onValueChange={(value) => handleReasonChange(itemId, 'reason', value)}
                >
                  <SelectTrigger className={errors[`reason_${itemId}`] ? 'border-red-500' : ''}>
                    <SelectValue placeholder="Select a reason" />
                  </SelectTrigger>
                  <SelectContent>
                    {returnReasons.map((reason) => (
                      <SelectItem key={reason.value} value={reason.value}>
                        {reason.label}
                        {reason.requiresPhotos && (
                          <span className="ml-2 text-xs text-red-600">(Photos required)</span>
                        )}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {errors[`reason_${itemId}`] && (
                  <p className="text-red-500 text-sm mt-1">{errors[`reason_${itemId}`]}</p>
                )}
              </div>

              {/* Reason Note */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Additional Details
                  {reasonValue === 'other' && <span className="text-red-600 ml-1">*</span>}
                </label>
                <Textarea
                  value={itemReason.note || ''}
                  onChange={(e) => handleReasonChange(itemId, 'note', e.target.value)}
                  placeholder="Please provide additional details about the issue..."
                  rows={3}
                  className={reasonValue === 'other' && !itemReason.note ? 'border-red-500' : ''}
                />
                {reasonValue === 'other' && !itemReason.note && (
                  <p className="text-red-500 text-sm mt-1">Details are required for "Other" reason</p>
                )}
              </div>

              {/* Photo Upload */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Photos
                  {requiresPhotos(reasonValue) && (
                    <span className="text-red-600 ml-1">*</span>
                  )}
                </label>
                
                {/* Photo Upload Button */}
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-4">
                  <div className="text-center">
                    <Camera className="mx-auto h-8 w-8 text-gray-400 mb-2" />
                    <div className="space-y-2">
                      <label htmlFor={`photo-upload-${itemId}`} className="cursor-pointer">
                        <Button
                          type="button"
                          variant="outline"
                          disabled={uploadingPhotos[itemId]}
                          asChild
                        >
                          <span>
                            <Upload className="h-4 w-4 mr-2" />
                            {uploadingPhotos[itemId] ? 'Uploading...' : 'Upload Photos'}
                          </span>
                        </Button>
                      </label>
                      <input
                        id={`photo-upload-${itemId}`}
                        type="file"
                        multiple
                        accept="image/*"
                        className="hidden"
                        onChange={(e) => handlePhotoUpload(itemId, e.target.files)}
                      />
                    </div>
                    <p className="text-xs text-gray-500 mt-2">
                      Upload up to 5 photos (JPG, PNG, max 5MB each)
                    </p>
                  </div>
                </div>

                {/* Uploaded Photos */}
                {photos.length > 0 && (
                  <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-3">
                    {photos.map((photoUrl, index) => (
                      <div key={index} className="relative group">
                        <img
                          src={photoUrl}
                          alt={`Return photo ${index + 1}`}
                          className="w-full h-20 object-cover rounded-lg"
                        />
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={() => removePhoto(itemId, photoUrl)}
                          className="absolute top-1 right-1 bg-red-600 text-white hover:bg-red-700 h-6 w-6 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
                        >
                          <X className="h-3 w-3" />
                        </Button>
                      </div>
                    ))}
                  </div>
                )}

                {/* Photo Requirement Error */}
                {errors[`photos_${itemId}`] && (
                  <Alert className="mt-2 border-red-200 bg-red-50">
                    <AlertCircle className="h-4 w-4 text-red-600" />
                    <AlertDescription className="text-red-800">
                      {errors[`photos_${itemId}`]}
                    </AlertDescription>
                  </Alert>
                )}

                {requiresPhotos(reasonValue) && (
                  <Alert className="mt-2 border-amber-200 bg-amber-50">
                    <AlertCircle className="h-4 w-4 text-amber-600" />
                    <AlertDescription className="text-amber-800">
                      Photos are required for {getReasonLabel(reasonValue)} returns. 
                      Please upload clear photos showing the issue.
                    </AlertDescription>
                  </Alert>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Summary */}
      <div className="bg-gray-50 rounded-lg p-4">
        <h4 className="font-medium text-gray-900 mb-3">Return Reasons Summary</h4>
        <div className="space-y-2">
          {formData.selectedItems.map((item) => {
            const itemId = item.id || item.fulfillment_line_item_id;
            const itemReason = formData.itemReasons?.[itemId];
            
            return (
              <div key={itemId} className="flex justify-between text-sm">
                <span className="text-gray-600 truncate">{item.title}</span>
                <span className={`font-medium ${itemReason?.reason ? 'text-green-600' : 'text-red-600'}`}>
                  {itemReason?.reason ? getReasonLabel(itemReason.reason) : 'Not specified'}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default ReturnReasonStep;