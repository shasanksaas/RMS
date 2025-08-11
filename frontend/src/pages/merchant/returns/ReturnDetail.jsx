import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { 
  ArrowLeft, Clock, User, Package, MessageSquare, CheckCircle, XCircle, 
  Printer, Mail, AlertTriangle, Truck, CreditCard, Home, Phone, ShoppingBag 
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../../components/ui/card';
import { Button } from '../../../components/ui/button';
import { Badge } from '../../../components/ui/badge';
import { Textarea } from '../../../components/ui/textarea';
import { Alert, AlertDescription } from '../../../components/ui/alert';

const ReturnDetail = () => {
  const { id } = useParams();
  const [returnRequest, setReturnRequest] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionNotes, setActionNotes] = useState('');
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState('');
  const [newComment, setNewComment] = useState('');

  // Get backend URL and tenant from environment  
  const backendUrl = process.env.REACT_APP_BACKEND_URL;
  const tenantId = 'tenant-rms34';

  const buildApiUrl = (endpoint) => {
    const apiUrl = backendUrl || 'http://localhost:8001';
    return `${apiUrl}${endpoint}`;
  };

  useEffect(() => {
    loadReturnDetails();
  }, [id]);

  const loadReturnDetails = async () => {
    try {
      setLoading(true);
      setError('');
      
      const response = await fetch(buildApiUrl(`/api/returns/${id}`), {
        headers: {
          'Content-Type': 'application/json',
          'X-Tenant-Id': tenantId
        }
      });

      if (response.ok) {
        const data = await response.json();
        setReturnRequest(data);
      } else if (response.status === 404) {
        setError('Return request not found');
      } else {
        setError(`Failed to load return details: ${response.statusText}`);
      }
    } catch (err) {
      console.error('Error loading return details:', err);
      setError('Unable to connect to server. Please check your connection.');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateStatus = async (newStatus, notes = '') => {
    setActionLoading(true);
    try {
      const response = await fetch(buildApiUrl(`/api/returns/${id}/status`), {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'X-Tenant-Id': tenantId
        },
        body: JSON.stringify({ 
          status: newStatus,
          notes: notes || actionNotes 
        })
      });

      if (response.ok) {
        await loadReturnDetails();
        setActionNotes('');
        setError('');
      } else {
        setError(`Failed to update status: ${response.statusText}`);
      }
    } catch (err) {
      console.error('Error updating status:', err);
      setError('Unable to update return status. Please try again.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleApprove = () => handleUpdateStatus('approved');
  const handleDeny = () => handleUpdateStatus('denied');
  const handleArchive = () => handleUpdateStatus('archived');
  const handleReject = () => handleUpdateStatus('rejected');

  const handleIssueLabel = async () => {
    setActionLoading(true);
    try {
      const response = await fetch(buildApiUrl(`/api/returns/${id}/label`), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Tenant-Id': tenantId
        }
      });

      if (response.ok) {
        const data = await response.json();
        
        // Download the label if URL provided
        if (data.label_url) {
          const link = document.createElement('a');
          link.href = data.label_url;
          link.download = `return_label_${id}.pdf`;
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
        }
        
        await loadReturnDetails();
        setError('');
      } else {
        setError(`Failed to generate label: ${response.statusText}`);
      }
    } catch (err) {
      console.error('Error issuing label:', err);
      setError('Unable to generate return label. Please try again.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleSendEmail = async () => {
    setActionLoading(true);
    try {
      const response = await fetch(buildApiUrl(`/api/returns/${id}/email`), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Tenant-Id': tenantId
        },
        body: JSON.stringify({
          type: 'status_update',
          message: actionNotes || 'Your return status has been updated.'
        })
      });

      if (response.ok) {
        await loadReturnDetails();
        setActionNotes('');
        setError('');
      } else {
        setError(`Failed to send email: ${response.statusText}`);
      }
    } catch (err) {
      console.error('Error sending email:', err);
      setError('Unable to send email notification. Please try again.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleProcessRefund = async () => {
    setActionLoading(true);
    try {
      const response = await fetch(buildApiUrl(`/api/returns/${id}/refund`), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Tenant-Id': tenantId
        },
        body: JSON.stringify({
          refund_method: returnRequest.refund_mode || 'original_payment'
        })
      });

      if (response.ok) {
        await loadReturnDetails();
        setError('');
      } else {
        setError(`Failed to process refund: ${response.statusText}`);
      }
    } catch (err) {
      console.error('Error processing refund:', err);
      setError('Unable to process refund. Please try again.');
    } finally {
      setActionLoading(false);
    }
  };

  const addComment = async () => {
    if (!newComment.trim()) return;
    
    try {
      const response = await fetch(buildApiUrl(`/api/returns/${id}/comments`), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Tenant-Id': tenantId
        },
        body: JSON.stringify({
          comment: newComment.trim(),
          internal: true // Comments are not shown to customers
        })
      });

      if (response.ok) {
        await loadReturnDetails();
        setNewComment('');
      } else {
        setError(`Failed to add comment: ${response.statusText}`);
      }
    } catch (err) {
      console.error('Error adding comment:', err);
      setError('Unable to add comment. Please try again.');
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center space-x-4">
          <Link to="/app/returns">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Returns
            </Button>
          </Link>
          <div className="animate-pulse">
            <div className="h-8 w-48 bg-gray-200 rounded" />
          </div>
        </div>
        <div className="animate-pulse space-y-4">
          <div className="h-96 bg-gray-200 rounded" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <Link to="/app/returns">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Returns
          </Button>
        </Link>
        <Alert className="border-red-200 bg-red-50">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription className="text-red-800">
            {error}
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  if (!returnRequest) {
    return (
      <div className="text-center py-12">
        <Package className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">Return not found</h3>
        <p className="text-gray-500">The return request you're looking for doesn't exist.</p>
        <Link to="/app/returns">
          <Button className="mt-4">Back to Returns</Button>
        </Link>
      </div>
    );
  }

  const getStatusColor = (status) => {
    const statusColors = {
      requested: 'bg-yellow-100 text-yellow-800 border-yellow-300',
      approved: 'bg-green-100 text-green-800 border-green-300',
      denied: 'bg-red-100 text-red-800 border-red-300',
      rejected: 'bg-red-100 text-red-800 border-red-300',
      processing: 'bg-blue-100 text-blue-800 border-blue-300',
      completed: 'bg-gray-100 text-gray-800 border-gray-300',
      archived: 'bg-gray-100 text-gray-800 border-gray-300'
    };
    return statusColors[status?.toLowerCase()] || statusColors.requested;
  };

  const formatCurrency = (amount, currency = 'USD') => {
    if (!amount && amount !== 0) return '₹ 0.00';
    const symbol = currency === 'INR' ? '₹' : '$';
    return `${symbol} ${Number(amount).toFixed(2)}`;
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString('en-IN', {
      year: 'numeric',
      month: 'short', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getRefundBreakdown = () => {
    const breakdown = returnRequest.estimated_refund?.breakdown || {};
    const currency = returnRequest.currency || 'INR';
    
    return {
      itemTotal: breakdown.item_total || 0,
      taxRefund: breakdown.tax_refund || 0,
      discount: breakdown.discount || 0,
      incentive: breakdown.incentive || 0,
      returnFee: breakdown.return_fee || breakdown.processing_fee || 0,
      finalAmount: returnRequest.estimated_refund?.amount || 0,
      currency
    };
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto p-6">
      {/* Header */}
      <div className="flex items-center justify-between border-b pb-4">
        <div className="flex items-center space-x-4">
          <Link to="/app/returns">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Returns
            </Button>
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">#{returnRequest.id?.slice(0, 8).toUpperCase()}</h1>
            <p className="text-gray-500">Order #{returnRequest.order_number}</p>
          </div>
        </div>
        <div className="flex items-center space-x-3">
          <Badge className={getStatusColor(returnRequest.status)}>
            {returnRequest.status?.replace('_', ' ').toUpperCase()}
          </Badge>
          {/* Admin actions */}
          <div className="flex items-center space-x-2">
            <Button size="sm" variant="outline" onClick={handleArchive} disabled={actionLoading}>
              Archive
            </Button>
            <Button size="sm" variant="outline" onClick={handleProcessRefund} disabled={actionLoading}>
              Refund
            </Button>
            <Button size="sm" variant="outline" className="text-red-600 hover:text-red-700">
              Delete
            </Button>
            <Button size="sm" variant="outline" onClick={handleReject} disabled={actionLoading}>
              Reject
            </Button>
          </div>
        </div>
      </div>

      {/* Shopify Integration Warning */}
      {returnRequest.shopify_sync_issues && (
        <Alert className="border-orange-200 bg-orange-50">
          <AlertTriangle className="h-4 w-4 text-orange-600" />
          <AlertDescription className="text-orange-800">
            This item is either unfulfilled or removed from the order on Shopify. This may cause issues while updating the status back to Shopify. Please check the status of this item on Shopify if you come across any issues.
          </AlertDescription>
        </Alert>
      )}

      {/* Product Deletion Warning */}
      {returnRequest.product_deleted && (
        <Alert className="border-red-200 bg-red-50">
          <AlertTriangle className="h-4 w-4 text-red-600" />
          <AlertDescription className="text-red-800">
            The product seems to be deleted from your Shopify store after the order was created. You cannot convert the request type in such cases, however, you can still delete this and create a new request.
          </AlertDescription>
        </Alert>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Main Content */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Status and Approval Info */}
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-2">
                  <Badge className={getStatusColor(returnRequest.status)}>
                    {returnRequest.status?.replace('_', ' ').toUpperCase()}
                  </Badge>
                  {returnRequest.decision_made_at && (
                    <span className="text-sm text-gray-500">
                      {returnRequest.status} {formatDate(returnRequest.decision_made_at)}
                    </span>
                  )}
                </div>
              </div>

              {/* Shipment Status */}
              <div className="space-y-3 mb-6">
                <h3 className="font-semibold text-gray-900">Shipment Status</h3>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">Requested refresh</span>
                  </div>
                  <div>
                    <span className="font-medium">Logistic Partner</span>
                    <p className="text-gray-700">{returnRequest.shipping?.carrier || 'Shipped by customer'}</p>
                  </div>
                  <div>
                    <span className="font-medium">Tracking ID</span>
                    <p className="text-gray-700">{returnRequest.shipping?.tracking_number || '_'}</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Items to Return */}
          <Card>
            <CardContent className="p-6">
              <div className="space-y-4">
                {(returnRequest.line_items || returnRequest.items || []).map((item, index) => (
                  <div key={index} className="flex items-start space-x-4 p-4 border rounded-lg">
                    <div className="w-16 h-16 bg-gray-100 rounded-lg flex items-center justify-center overflow-hidden">
                      {item.image_url ? (
                        <img src={item.image_url} alt={item.title} className="w-full h-full object-cover" />
                      ) : (
                        <Package className="h-8 w-8 text-gray-400" />
                      )}
                    </div>
                    <div className="flex-1">
                      <h4 className="font-medium text-gray-900">{item.title || item.product_name}</h4>
                      <p className="text-sm text-gray-500">
                        {formatCurrency(item.unit_price || item.price, getRefundBreakdown().currency)} x {item.quantity}
                      </p>
                      <p className="text-sm text-gray-600">Price incl. of discount & taxes</p>
                    </div>
                    <div className="text-right">
                      <p className="font-bold text-lg">
                        {formatCurrency((item.unit_price || item.price) * item.quantity, getRefundBreakdown().currency)}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Price Breakdown */}
          <Card>
            <CardContent className="p-6">
              <h3 className="font-semibold text-gray-900 mb-4">Price Breakdown</h3>
              <div className="space-y-3">
                {(() => {
                  const breakdown = getRefundBreakdown();
                  return (
                    <>
                      <div className="flex justify-between text-sm">
                        <span>Item price</span>
                        <span>{formatCurrency(breakdown.itemTotal, breakdown.currency)}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span>Incentive</span>
                        <span className="text-green-600">+ {formatCurrency(breakdown.incentive, breakdown.currency)}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span>Tax</span>
                        <span className="text-green-600">+ {formatCurrency(breakdown.taxRefund, breakdown.currency)}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span>Discount</span>
                        <span className="text-red-600">- {formatCurrency(Math.abs(breakdown.discount), breakdown.currency)}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span>Return Fee</span>
                        <span className="text-red-600">- {formatCurrency(Math.abs(breakdown.returnFee), breakdown.currency)}</span>
                      </div>
                      <div className="border-t pt-3">
                        <div className="flex justify-between font-bold text-lg">
                          <span>Total (To be refunded)</span>
                          <span>{formatCurrency(breakdown.finalAmount, breakdown.currency)}</span>
                        </div>
                      </div>
                    </>
                  );
                })()}
              </div>
            </CardContent>
          </Card>

          {/* Timeline */}
          <Card>
            <CardHeader>
              <CardTitle>Timeline</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {/* Comment Input */}
                <div className="flex space-x-3">
                  <div className="flex-1">
                    <Textarea
                      placeholder="Leave a comment.."
                      value={newComment}
                      onChange={(e) => setNewComment(e.target.value)}
                      rows={3}
                      className="resize-none"
                    />
                    <p className="text-xs text-gray-500 mt-1">Comments are not shown to customers</p>
                  </div>
                  <Button onClick={addComment} disabled={!newComment.trim() || actionLoading}>
                    Add
                  </Button>
                </div>

                {/* Timeline Events */}
                <div className="space-y-4 mt-6">
                  {(returnRequest.audit_log || []).map((event, index) => (
                    <div key={index} className="border-l-4 border-blue-200 pl-4">
                      <div className="flex items-start justify-between">
                        <div>
                          <p className="font-medium text-gray-900">{event.description || event.action}</p>
                          <p className="text-sm text-gray-600">{formatDate(event.timestamp)}</p>
                        </div>
                        <span className="text-xs bg-gray-100 px-2 py-1 rounded">
                          {event.performed_by === 'system' ? 'SYSTEM' : 'ADMIN'}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Sidebar */}
        <div className="space-y-6">
          {/* Actions */}
          {returnRequest.status === 'requested' && (
            <Card>
              <CardHeader>
                <CardTitle>Actions</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <Textarea
                    placeholder="Add notes for this action..."
                    value={actionNotes}
                    onChange={(e) => setActionNotes(e.target.value)}
                    rows={3}
                  />
                  <div className="space-y-2">
                    <Button 
                      onClick={handleApprove} 
                      className="w-full bg-green-600 hover:bg-green-700"
                      disabled={actionLoading}
                    >
                      <CheckCircle className="h-4 w-4 mr-2" />
                      Approve Return
                    </Button>
                    <Button 
                      variant="outline" 
                      onClick={handleDeny} 
                      className="w-full"
                      disabled={actionLoading}
                    >
                      <XCircle className="h-4 w-4 mr-2" />
                      Deny Return
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Customer Information */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <User className="h-5 w-5" />
                <span>Customer</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <h4 className="font-semibold text-lg">{returnRequest.customer_name || 'N/A'}</h4>
                </div>

                <div>
                  <h5 className="font-medium text-gray-900 mb-2">Contact Information</h5>
                  <div className="space-y-2 text-sm">
                    <div className="flex items-center space-x-2">
                      <Mail className="h-4 w-4 text-gray-400" />
                      <span>{returnRequest.customer_email || 'No email provided'}</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Phone className="h-4 w-4 text-gray-400" />
                      <span>{returnRequest.customer_phone || 'No phone provided'}</span>
                    </div>
                  </div>
                </div>

                <div>
                  <h5 className="font-medium text-gray-900 mb-2">Refund Mode</h5>
                  <p className="text-sm text-blue-600 font-medium">
                    {returnRequest.refund_mode || 'Store Credit'}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    Order was originally paid using {returnRequest.payment_method || 'manual payment gateway'}
                  </p>
                </div>

                <div>
                  <h5 className="font-medium text-gray-900 mb-2">Return Method</h5>
                  <div className="flex items-center space-x-2">
                    <Truck className="h-4 w-4 text-gray-400" />
                    <span className="text-sm font-medium">
                      {returnRequest.return_method === 'prepaid_label' ? 'Send a return label' : 
                       returnRequest.return_method === 'customer_ships' ? 'Ship back myself' : 
                       returnRequest.return_method || 'Ship back myself'}
                    </span>
                  </div>
                  {returnRequest.return_method_original && (
                    <p className="text-xs text-gray-500 mt-1">
                      The customer originally chose {returnRequest.return_method_original} as return method.
                    </p>
                  )}
                </div>

                <div>
                  <h5 className="font-medium text-gray-900 mb-2">Customer's address</h5>
                  <div className="flex items-start space-x-2">
                    <Home className="h-4 w-4 text-gray-400 mt-1" />
                    <div className="text-sm">
                      <p>{returnRequest.customer_name}</p>
                      {returnRequest.shipping_address && (
                        <>
                          <p>{returnRequest.shipping_address.address1}</p>
                          <p>{returnRequest.shipping_address.city}, {returnRequest.shipping_address.province}</p>
                          <p>{returnRequest.shipping_address.country}</p>
                        </>
                      )}
                    </div>
                  </div>
                </div>

                <div>
                  <h5 className="font-medium text-gray-900 mb-2">Notes</h5>
                  <p className="text-sm text-gray-600">
                    {returnRequest.customer_note || returnRequest.notes || 'No notes added'}
                  </p>
                </div>

                <div>
                  <h5 className="font-medium text-gray-900 mb-2">Reason</h5>
                  <p className="text-sm text-gray-600">
                    {returnRequest.line_items?.[0]?.reason || returnRequest.reason || returnRequest.return_reason_category || 'Received damaged item'}
                  </p>
                </div>

                <div>
                  <h5 className="font-medium text-gray-900 mb-2">Tags</h5>
                  <div className="flex flex-wrap gap-2">
                    <input 
                      type="text" 
                      placeholder="Type the tag and press enter on your keyboard"
                      className="text-sm border-0 border-b border-gray-300 focus:border-blue-500 outline-none bg-transparent"
                    />
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Additional Actions */}
          {returnRequest.status === 'approved' && (
            <Card>
              <CardHeader>
                <CardTitle>Next Steps</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <Button 
                    onClick={handleIssueLabel} 
                    className="w-full"
                    disabled={actionLoading}
                  >
                    <Printer className="h-4 w-4 mr-2" />
                    Generate Return Label
                  </Button>
                  <Button 
                    variant="outline" 
                    onClick={handleSendEmail} 
                    className="w-full"
                    disabled={actionLoading}
                  >
                    <Mail className="h-4 w-4 mr-2" />
                    Send Email Update
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};

export default ReturnDetail;