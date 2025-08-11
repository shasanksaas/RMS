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
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Link to="/app/returns">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Returns
            </Button>
          </Link>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Return {returnRequest.id}</h1>
            <p className="text-gray-500">Order {returnRequest.order_number}</p>
          </div>
        </div>
        <Badge className={getStatusColor(returnRequest.status)}>
          {returnRequest.status.toUpperCase()}
        </Badge>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Customer Information */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <User className="h-5 w-5" />
                <span>Customer Information</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="font-medium">Name</span>
                  <span>{returnRequest.customer_name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="font-medium">Email</span>
                  <span>{returnRequest.customer_email}</span>
                </div>
                <div className="flex justify-between">
                  <span className="font-medium">Order Number</span>
                  <span className="font-mono">{returnRequest.order_number}</span>
                </div>
                <div className="flex justify-between">
                  <span className="font-medium">Request Date</span>
                  <span>{new Date(returnRequest.created_at).toLocaleString()}</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Items to Return */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Package className="h-5 w-5" />
                <span>Items to Return</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {returnRequest.items.map((item, index) => (
                  <div key={index} className="flex items-center space-x-4 p-4 border rounded-lg">
                    <div className="w-16 h-16 bg-gray-200 rounded-lg flex items-center justify-center">
                      <Package className="h-6 w-6 text-gray-400" />
                    </div>
                    <div className="flex-1">
                      <h4 className="font-medium">{item.product_name}</h4>
                      <p className="text-sm text-gray-500">SKU: {item.product_sku}</p>
                      <p className="text-sm text-gray-500">Reason: {item.reason}</p>
                    </div>
                    <div className="text-right">
                      <p className="font-medium">Qty: {item.quantity}</p>
                      <p className="text-lg font-bold">${item.price}</p>
                    </div>
                  </div>
                ))}
                <div className="border-t pt-4">
                  <div className="flex justify-between text-lg font-bold">
                    <span>Total Refund Amount</span>
                    <span>${returnRequest.refund_amount}</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Rule Explanation */}
          {returnRequest.rule_explanation && (
            <Card>
              <CardHeader>
                <CardTitle>Rule Evaluation</CardTitle>
                <CardDescription>
                  Automated rule processing and recommendation
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {returnRequest.rule_explanation.steps.map((step, index) => (
                    <div key={index} className="flex items-start space-x-3 p-3 border rounded-lg">
                      <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                        step.result === 'PASS' ? 'bg-green-100 text-green-800' :
                        step.result === 'FAIL' ? 'bg-red-100 text-red-800' :
                        'bg-yellow-100 text-yellow-800'
                      }`}>
                        {step.result === 'PASS' ? '✓' : step.result === 'FAIL' ? '✗' : '?'}
                      </div>
                      <div>
                        <h4 className="font-medium">{step.rule}</h4>
                        <p className="text-sm text-gray-600">{step.explanation}</p>
                      </div>
                    </div>
                  ))}
                  <Alert>
                    <AlertDescription>
                      <strong>Recommendation:</strong> {returnRequest.rule_explanation.recommendation}
                    </AlertDescription>
                  </Alert>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Customer Notes */}
          {returnRequest.notes && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <MessageSquare className="h-5 w-5" />
                  <span>Customer Notes</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-700">{returnRequest.notes}</p>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Actions */}
          {returnRequest.status === 'requested' && (
            <Card>
              <CardHeader>
                <CardTitle>Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <Textarea
                  placeholder="Add notes for this action..."
                  value={actionNotes}
                  onChange={(e) => setActionNotes(e.target.value)}
                  rows={3}
                />
                <div className="space-y-2">
                  <Button 
                    onClick={handleApprove} 
                    className="w-full"
                    disabled={actionLoading}
                  >
                    {actionLoading ? (
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                    ) : (
                      <CheckCircle className="h-4 w-4 mr-2" />
                    )}
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
              </CardContent>
            </Card>
          )}

          {returnRequest.status === 'approved' && (
            <Card>
              <CardHeader>
                <CardTitle>Next Steps</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Button 
                  onClick={handleIssueLabel} 
                  className="w-full"
                  disabled={actionLoading}
                >
                  {actionLoading ? (
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                  ) : (
                    <Printer className="h-4 w-4 mr-2" />
                  )}
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
              </CardContent>
            </Card>
          )}

          {/* Timeline */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Clock className="h-5 w-5" />
                <span>Timeline</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {timeline.map((event, index) => (
                  <div key={event.id} className="flex items-start space-x-3">
                    <div className="w-2 h-2 bg-blue-600 rounded-full mt-2" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900">{event.event}</p>
                      <p className="text-sm text-gray-500">{event.description}</p>
                      <p className="text-xs text-gray-400">
                        {new Date(event.timestamp).toLocaleString()} • {event.user}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default ReturnDetail;