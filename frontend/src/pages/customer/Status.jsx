import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { CheckCircle, Clock, Truck, Package, Download, Mail, RefreshCw } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { Alert, AlertDescription } from '../../components/ui/alert';

const Status = () => {
  const { returnId } = useParams();
  const [returnRequest, setReturnRequest] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchReturnData();
  }, [returnId]);

  const fetchReturnData = async () => {
    try {
      setLoading(true);
      const response = await fetch(
        `${process.env.REACT_APP_BACKEND_URL}/api/returns/${returnId}`,
        {
          headers: {
            'Content-Type': 'application/json',
            'X-Tenant-Id': localStorage.getItem('currentTenant') || 'tenant-rms34'
          }
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch return data');
      }

      const data = await response.json();
      
      // Transform API data to match component expectations
      const transformedData = {
        id: data.id,
        orderNumber: data.order_number,
        status: data.status?.toLowerCase(),
        resolution: {
          type: 'refund',
          title: 'Refund to Original Payment',
          amount: typeof data.estimated_refund === 'object' 
            ? parseFloat(data.estimated_refund.amount || 0)
            : parseFloat(data.estimated_refund || 0)
        },
        items: (data.line_items || []).map(item => ({
          productName: item.title || 'Product',
          quantity: item.quantity || 1,
          reason: item.reason?.description || item.reason?.code || 'Not specified',
          refundAmount: typeof item.unit_price === 'object' 
            ? parseFloat(item.unit_price.amount || 0)
            : parseFloat(item.unit_price || 0)
        })),
        customer: {
          name: data.customer_name,
          email: data.customer_email
        },
        created_at: data.created_at,
        timeline: generateTimelineFromStatus(data.status, data.audit_log || [])
      };
      
      setReturnRequest(transformedData);
    } catch (error) {
      console.error('Error fetching return data:', error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const generateTimelineFromStatus = (currentStatus, auditLog) => {
    const timeline = [
      {
        id: 1,
        title: 'Return Requested',
        description: 'Your return request has been submitted and is being reviewed',
        status: 'completed',
        timestamp: null,
        icon: Package
      }
    ];

    // Add timeline items based on status
    const status = currentStatus?.toLowerCase();
    
    if (['approved', 'processing', 'completed'].includes(status)) {
      timeline.push({
        id: 2,
        title: 'Return Approved',
        description: 'Your return has been approved. A return label has been generated',
        status: 'completed',
        timestamp: null,
        icon: CheckCircle
      });
    }

    if (['processing', 'completed'].includes(status)) {
      timeline.push({
        id: 3,
        title: 'Return Label Issued',
        description: 'Print your return label and ship your items back to us',
        status: status === 'processing' ? 'current' : 'completed',
        timestamp: null,
        icon: Download,
        actionable: status === 'processing'
      });
    }

    if (status === 'completed') {
      timeline.push({
        id: 4,
        title: 'Items in Transit',
        description: 'We\'ll update you when we receive your return package',
        status: 'completed',
        timestamp: null,
        icon: Truck
      });

      timeline.push({
        id: 5,
        title: 'Return Processed',
        description: 'Your refund has been processed',
        status: 'completed',
        timestamp: null,
        icon: RefreshCw
      });
    } else {
      timeline.push({
        id: 4,
        title: 'Items in Transit',
        description: 'We\'ll update you when we receive your return package',
        status: 'pending',
        timestamp: null,
        icon: Truck
      });

      timeline.push({
        id: 5,
        title: 'Return Processed',
        description: 'Your refund will be issued once we process your return',
        status: 'pending',
        timestamp: null,
        icon: RefreshCw
      });
    }

    // Add timestamps from audit log if available
    auditLog.forEach(entry => {
      if (entry.action === 'return_created' && timeline[0]) {
        timeline[0].timestamp = entry.timestamp;
      }
      if (entry.action?.includes('status_updated') && entry.details?.new_status === 'APPROVED' && timeline[1]) {
        timeline[1].timestamp = entry.timestamp;
      }
    });

    return timeline;
  };
  const getStatusBadge = (status) => {
    const config = {
      requested: { color: 'bg-yellow-100 text-yellow-800', label: 'Pending Review' },
      approved: { color: 'bg-blue-100 text-blue-800', label: 'Approved' },
      denied: { color: 'bg-red-100 text-red-800', label: 'Denied' },
      processing: { color: 'bg-purple-100 text-purple-800', label: 'Processing' },
      completed: { color: 'bg-green-100 text-green-800', label: 'Complete' },
      cancelled: { color: 'bg-gray-100 text-gray-800', label: 'Cancelled' }
    };
    
    const { color, label } = config[status] || config.requested;
    return <Badge className={color}>{label}</Badge>;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-pulse">
            <Package className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          </div>
          <p className="text-gray-600">Loading your return status...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Alert className="max-w-md">
            <AlertDescription>
              Unable to load return status: {error}
            </AlertDescription>
          </Alert>
        </div>
      </div>
    );
  }

  if (!returnRequest) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Alert className="max-w-md">
            <AlertDescription>
              Return not found. Please check your return ID and try again.
            </AlertDescription>
          </Alert>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Return Status
          </h1>
          <p className="text-gray-600">
            Track the progress of your return request
          </p>
        </div>

        {/* Return Overview Card */}
        <Card className="mb-8">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-xl">
                  Return #{returnRequest.id.slice(-8)}
                </CardTitle>
                <CardDescription>
                  Order: {returnRequest.orderNumber}
                </CardDescription>
              </div>
              <div className="text-right">
                {getStatusBadge(returnRequest.status)}
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Resolution */}
              <div>
                <h3 className="text-sm font-medium text-gray-500 mb-2">Resolution</h3>
                <div className="text-lg font-semibold">
                  {returnRequest.resolution.title}
                </div>
                <div className="text-2xl font-bold text-green-600 mt-1">
                  ${returnRequest.resolution.amount.toFixed(2)}
                </div>
              </div>

              {/* Items Count */}
              <div>
                <h3 className="text-sm font-medium text-gray-500 mb-2">Items</h3>
                <div className="text-lg font-semibold">
                  {returnRequest.items.length} item{returnRequest.items.length !== 1 ? 's' : ''}
                </div>
              </div>

              {/* Estimated Completion */}
              <div>
                <h3 className="text-sm font-medium text-gray-500 mb-2">Estimated Completion</h3>
                <div className="text-lg font-semibold">
                  {returnRequest.status === 'completed' ? 'Completed' : '7-10 business days'}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Timeline */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Return Progress</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              {returnRequest.timeline.map((step, index) => (
                <div key={step.id} className="flex items-start">
                  <div className="flex-shrink-0">
                    <div className={`
                      w-10 h-10 rounded-full flex items-center justify-center
                      ${step.status === 'completed' 
                        ? 'bg-green-100 text-green-600' 
                        : step.status === 'current' 
                        ? 'bg-blue-100 text-blue-600' 
                        : 'bg-gray-100 text-gray-400'
                      }
                    `}>
                      <step.icon className="h-5 w-5" />
                    </div>
                  </div>
                  <div className="ml-4 flex-1">
                    <div className="flex items-center justify-between">
                      <h3 className={`text-lg font-medium ${
                        step.status === 'completed' ? 'text-green-600' : 
                        step.status === 'current' ? 'text-blue-600' : 'text-gray-500'
                      }`}>
                        {step.title}
                      </h3>
                      {step.timestamp && (
                        <span className="text-sm text-gray-500">
                          {new Date(step.timestamp).toLocaleDateString()}
                        </span>
                      )}
                    </div>
                    <p className="text-gray-600 mt-1">{step.description}</p>
                    {step.actionable && (
                      <Button className="mt-3" size="sm">
                        <Download className="h-4 w-4 mr-2" />
                        Download Return Label
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Items Being Returned */}
        <Card>
          <CardHeader>
            <CardTitle>Items Being Returned</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {returnRequest.items.map((item, index) => (
                <div key={index} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div className="flex-1">
                    <h4 className="font-medium">{item.productName}</h4>
                    <p className="text-sm text-gray-600">
                      Qty: {item.quantity} • Reason: {item.reason}
                    </p>
                  </div>
                  <div className="text-right">
                    <div className="font-semibold">${item.refundAmount.toFixed(2)}</div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Status;
              <CardDescription>Order {returnRequest.orderNumber}</CardDescription>
            </div>
            {getStatusBadge(returnRequest.status)}
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <h4 className="font-medium text-gray-900">Resolution</h4>
              <p className="text-sm text-gray-600">{returnRequest.resolution.title}</p>
              <p className="text-lg font-bold">${returnRequest.resolution.amount.toFixed(2)}</p>
            </div>
            <div>
              <h4 className="font-medium text-gray-900">Items</h4>
              <p className="text-sm text-gray-600">{returnRequest.items.length} item(s)</p>
            </div>
            <div>
              <h4 className="font-medium text-gray-900">Estimated Completion</h4>
              <p className="text-sm text-gray-600">
                {new Date(returnRequest.estimatedCompletion).toLocaleDateString()}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Current Action Required */}
      {returnRequest.status === 'approved' && (
        <Alert className="border-blue-200 bg-blue-50">
          <Download className="h-4 w-4" />
          <AlertDescription>
            <div className="flex items-center justify-between">
              <div>
                <strong>Action Required:</strong> Download your return label and ship your items back to us.
              </div>
              <Button onClick={downloadLabel} size="sm">
                <Download className="h-4 w-4 mr-2" />
                Download Label
              </Button>
            </div>
          </AlertDescription>
        </Alert>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Timeline */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Clock className="h-5 w-5" />
                <span>Return Timeline</span>
              </CardTitle>
              <CardDescription>Track the progress of your return</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {returnRequest.timeline.map((step, index) => {
                  const Icon = step.icon;
                  const isCompleted = step.status === 'completed';
                  const isCurrent = step.status === 'current';
                  const isPending = step.status === 'pending';
                  
                  return (
                    <div key={step.id} className="flex items-start space-x-4">
                      {/* Icon */}
                      <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                        isCompleted ? 'bg-green-100' : 
                        isCurrent ? 'bg-blue-100' : 
                        'bg-gray-100'
                      }`}>
                        <Icon className={`h-5 w-5 ${
                          isCompleted ? 'text-green-600' : 
                          isCurrent ? 'text-blue-600' : 
                          'text-gray-400'
                        }`} />
                      </div>

                      {/* Content */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-3">
                          <h3 className={`text-lg font-medium ${
                            isPending ? 'text-gray-400' : 'text-gray-900'
                          }`}>
                            {step.title}
                          </h3>
                          {isCompleted && (
                            <CheckCircle className="h-5 w-5 text-green-600" />
                          )}
                        </div>
                        <p className={`text-sm mt-1 ${
                          isPending ? 'text-gray-400' : 'text-gray-600'
                        }`}>
                          {step.description}
                        </p>
                        {step.timestamp && (
                          <p className="text-xs text-gray-400 mt-2">
                            {new Date(step.timestamp).toLocaleString()}
                          </p>
                        )}
                        
                        {step.actionable && isCurrent && (
                          <div className="mt-3">
                            <Button onClick={downloadLabel} size="sm">
                              <Download className="h-4 w-4 mr-2" />
                              Download Label
                            </Button>
                          </div>
                        )}
                      </div>

                      {/* Connecting Line */}
                      {index < returnRequest.timeline.length - 1 && (
                        <div className={`absolute left-5 mt-10 h-6 w-0.5 ${
                          isCompleted ? 'bg-green-200' : 'bg-gray-200'
                        }`} />
                      )}
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Items Summary */}
          <Card>
            <CardHeader>
              <CardTitle>Items Being Returned</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {returnRequest.items.map((item, index) => (
                  <div key={index} className="flex items-center space-x-3 p-3 bg-gray-50 rounded">
                    <Package className="h-8 w-8 text-gray-400" />
                    <div className="flex-1 min-w-0">
                      <h4 className="font-medium text-sm">{item.productName}</h4>
                      <p className="text-xs text-gray-500">Qty: {item.quantity}</p>
                      <p className="text-xs text-gray-500">Reason: {item.reason}</p>
                    </div>
                    <span className="font-medium">${item.refundAmount}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Help & Support */}
          <Card>
            <CardHeader>
              <CardTitle>Need Help?</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <Button variant="outline" className="w-full">
                <Mail className="h-4 w-4 mr-2" />
                Contact Support
              </Button>
              <div className="text-sm text-gray-600">
                <p>Questions about your return?</p>
                <p>Our support team is here to help!</p>
              </div>
            </CardContent>
          </Card>

          {/* Tracking Number */}
          {returnRequest.trackingNumber && (
            <Card>
              <CardHeader>
                <CardTitle>Tracking Information</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-sm">
                  <p className="font-medium">Tracking Number:</p>
                  <p className="font-mono text-blue-600">{returnRequest.trackingNumber}</p>
                  <Button variant="outline" size="sm" className="mt-2 w-full">
                    <Truck className="h-4 w-4 mr-2" />
                    Track Package
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

export default Status;