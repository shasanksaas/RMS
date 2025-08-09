import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Clock, User, Package, MessageSquare, CheckCircle, XCircle, Printer, Mail } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../../components/ui/card';
import { Button } from '../../../components/ui/button';
import { Badge } from '../../../components/ui/badge';
import { Textarea } from '../../../components/ui/textarea';
import { Alert, AlertDescription } from '../../../components/ui/alert';

const ReturnDetail = () => {
  const { id } = useParams();
  const [returnRequest, setReturnRequest] = useState(null);
  const [timeline, setTimeline] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionNotes, setActionNotes] = useState('');

  useEffect(() => {
    // Mock data - replace with real API call
    const mockReturn = {
      id: 'RET-001',
      orderNumber: 'ORD-12345',
      customer: {
        name: 'Sarah Johnson',
        email: 'sarah@example.com'
      },
      status: 'requested',
      reason: 'wrong_size',
      refundAmount: 49.99,
      createdAt: '2024-01-15T10:30:00Z',
      items: [
        {
          productName: 'Blue Cotton T-Shirt',
          productSku: 'SHIRT-001',
          quantity: 1,
          price: 49.99,
          reason: 'Size too small'
        }
      ],
      notes: 'Customer mentioned the medium size feels like a small. Would like to exchange for large.',
      ruleExplanation: {
        steps: [
          {
            rule: 'Return Window Check',
            result: 'PASS',
            explanation: 'Order placed 3 days ago, within 30-day window'
          },
          {
            rule: 'Product Eligibility',
            result: 'PASS',
            explanation: 'Clothing items are eligible for size exchanges'
          },
          {
            rule: 'Auto-approve Rules',
            result: 'PENDING',
            explanation: 'Size exchanges require manual review'
          }
        ],
        finalDecision: 'PENDING_REVIEW',
        recommendation: 'Approve - standard size exchange'
      }
    };

    const mockTimeline = [
      {
        id: 1,
        event: 'Return requested',
        description: 'Customer submitted return request',
        status: 'requested',
        timestamp: '2024-01-15T10:30:00Z',
        user: 'Customer'
      },
      {
        id: 2,
        event: 'Rule evaluation completed',
        description: 'Return routed to manual review',
        status: 'requested',
        timestamp: '2024-01-15T10:31:00Z',
        user: 'System'
      }
    ];

    setReturnRequest(mockReturn);
    setTimeline(mockTimeline);
    setLoading(false);
  }, [id]);

  const handleApprove = async () => {
    console.log('Approving return', id, { notes: actionNotes });
    // Implementation for approving return
  };

  const handleDeny = async () => {
    console.log('Denying return', id, { notes: actionNotes });
    // Implementation for denying return
  };

  const handleIssueLabel = async () => {
    console.log('Issuing return label for', id);
    // Implementation for label generation
  };

  if (loading) {
    return <div className="animate-pulse space-y-4">
      <div className="h-8 bg-gray-200 rounded" />
      <div className="h-96 bg-gray-200 rounded" />
    </div>;
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
    const colors = {
      requested: 'bg-yellow-100 text-yellow-800',
      approved: 'bg-blue-100 text-blue-800',
      denied: 'bg-red-100 text-red-800',
      resolved: 'bg-green-100 text-green-800'
    };
    return colors[status] || colors.requested;
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
            <p className="text-gray-500">Order {returnRequest.orderNumber}</p>
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
                  <span>{returnRequest.customer.name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="font-medium">Email</span>
                  <span>{returnRequest.customer.email}</span>
                </div>
                <div className="flex justify-between">
                  <span className="font-medium">Order Number</span>
                  <span className="font-mono">{returnRequest.orderNumber}</span>
                </div>
                <div className="flex justify-between">
                  <span className="font-medium">Request Date</span>
                  <span>{new Date(returnRequest.createdAt).toLocaleString()}</span>
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
                      <h4 className="font-medium">{item.productName}</h4>
                      <p className="text-sm text-gray-500">SKU: {item.productSku}</p>
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
                    <span>${returnRequest.refundAmount}</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Rule Explanation */}
          <Card>
            <CardHeader>
              <CardTitle>Rule Evaluation</CardTitle>
              <CardDescription>
                Automated rule processing and recommendation
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {returnRequest.ruleExplanation.steps.map((step, index) => (
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
                    <strong>Recommendation:</strong> {returnRequest.ruleExplanation.recommendation}
                  </AlertDescription>
                </Alert>
              </div>
            </CardContent>
          </Card>

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
                  <Button onClick={handleApprove} className="w-full">
                    <CheckCircle className="h-4 w-4 mr-2" />
                    Approve Return
                  </Button>
                  <Button variant="outline" onClick={handleDeny} className="w-full">
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
                <Button onClick={handleIssueLabel} className="w-full">
                  <Printer className="h-4 w-4 mr-2" />
                  Generate Return Label
                </Button>
                <Button variant="outline" className="w-full">
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