import React, { useState, useEffect } from 'react';
import { useParams, useLocation, useNavigate } from 'react-router-dom';
import { 
  CheckCircle, 
  Package, 
  Mail, 
  Download, 
  Truck, 
  Calendar,
  ArrowRight,
  AlertCircle
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Alert, AlertDescription } from '../../components/ui/alert';
import { Badge } from '../../components/ui/badge';

const ReturnConfirmation = () => {
  const { returnId } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  
  const [returnData, setReturnData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Get data from navigation state if available
  const stateData = location.state?.returnData;
  const message = location.state?.message;

  useEffect(() => {
    if (stateData) {
      setReturnData(stateData);
      setLoading(false);
    } else {
      // Fetch return data if not available in state
      fetchReturnData();
    }
  }, [returnId, stateData]);

  const fetchReturnData = async () => {
    try {
      const response = await fetch(
        `${process.env.REACT_APP_BACKEND_URL}/api/returns/${returnId}`,
        {
          headers: {
            'X-Tenant-Id': localStorage.getItem('currentTenant') || 'tenant-rms34'
          }
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch return data');
      }

      const data = await response.json();
      setReturnData(data);
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-pulse">
            <Package className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          </div>
          <p className="text-gray-600">Loading your return confirmation...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md">
          <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            Unable to Load Return Information
          </h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <Button onClick={() => navigate('/returns')}>
            Return to Portal
          </Button>
        </div>
      </div>
    );
  }

  const isAutoApproved = returnData?.status === 'approved';
  const hasLabel = returnData?.label_url;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="container mx-auto px-4 py-6">
          <div className="text-center">
            <CheckCircle className="h-16 w-16 text-green-600 mx-auto mb-4" />
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              Return Request Submitted Successfully!
            </h1>
            <p className="text-gray-600 text-lg">
              Return ID: <span className="font-mono font-semibold">{returnId}</span>
            </p>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8 space-y-8">
        {/* Success Message */}
        {message && (
          <Alert className="border-green-200 bg-green-50">
            <CheckCircle className="h-4 w-4 text-green-600" />
            <AlertDescription className="text-green-800">
              {message}
            </AlertDescription>
          </Alert>
        )}

        {/* Status and Next Steps */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Return Status */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Package className="h-5 w-5 text-blue-600" />
                <span>Return Status</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-gray-600">Current Status:</span>
                <Badge 
                  variant={isAutoApproved ? 'default' : 'secondary'}
                  className="text-sm"
                >
                  {isAutoApproved ? 'Approved' : 'Under Review'}
                </Badge>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-gray-600">Estimated Refund:</span>
                <span className="font-semibold text-green-600 text-lg">
                  ${returnData?.estimated_refund?.toFixed(2) || '0.00'}
                </span>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-gray-600">Processing Time:</span>
                <span className="text-gray-900">
                  {isAutoApproved ? '1-2 business days' : '2-3 business days'}
                </span>
              </div>

              {returnData?.tracking_number && (
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">Tracking Number:</span>
                  <span className="font-mono text-sm bg-gray-100 px-2 py-1 rounded">
                    {returnData.tracking_number}
                  </span>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Next Steps */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <ArrowRight className="h-5 w-5 text-blue-600" />
                <span>What Happens Next</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-start space-x-3">
                  <div className="w-6 h-6 bg-green-600 text-white rounded-full flex items-center justify-center text-xs font-medium">
                    ✓
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-900">Request Submitted</h4>
                    <p className="text-sm text-gray-600">Your return request has been received and logged in our system.</p>
                  </div>
                </div>
                
                <div className="flex items-start space-x-3">
                  <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium ${
                    isAutoApproved 
                      ? 'bg-green-600 text-white' 
                      : 'bg-blue-600 text-white'
                  }`}>
                    {isAutoApproved ? '✓' : '2'}
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-900">
                      {isAutoApproved ? 'Approved' : 'Under Review'}
                    </h4>
                    <p className="text-sm text-gray-600">
                      {isAutoApproved 
                        ? 'Your return has been automatically approved.'
                        : 'Our team is reviewing your return request.'
                      }
                    </p>
                  </div>
                </div>
                
                <div className="flex items-start space-x-3">
                  <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium ${
                    hasLabel 
                      ? 'bg-green-600 text-white' 
                      : 'bg-gray-300 text-gray-600'
                  }`}>
                    {hasLabel ? '✓' : '3'}
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-900">Return Instructions</h4>
                    <p className="text-sm text-gray-600">
                      {hasLabel 
                        ? 'Your return label is ready for download.'
                        : 'You\'ll receive return shipping instructions via email.'
                      }
                    </p>
                  </div>
                </div>
                
                <div className="flex items-start space-x-3">
                  <div className="w-6 h-6 bg-gray-300 text-gray-600 rounded-full flex items-center justify-center text-xs font-medium">
                    4
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-900">Refund Processing</h4>
                    <p className="text-sm text-gray-600">
                      Once we receive your items, your refund will be processed within 3-5 business days.
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Action Buttons */}
        {hasLabel && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Download className="h-5 w-5 text-blue-600" />
                <span>Return Label</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">Your prepaid return label is ready</h4>
                  <p className="text-sm text-gray-600">
                    Download and print your prepaid return label, then attach it to your package.
                  </p>
                </div>
                <Button asChild>
                  <a href={returnData.label_url} download>
                    <Download className="h-4 w-4 mr-2" />
                    Download Label
                  </a>
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Email Confirmation */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Mail className="h-5 w-5 text-blue-600" />
              <span>Email Confirmation</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-start space-x-4">
              <div className="flex-1">
                <h4 className="font-medium text-gray-900 mb-2">
                  Confirmation sent to your email
                </h4>
                <p className="text-sm text-gray-600 mb-4">
                  We've sent a detailed confirmation email with your return information 
                  and next steps. If you don't see it in your inbox, please check your spam folder.
                </p>
                <div className="flex items-center text-sm text-gray-500">
                  <Calendar className="h-4 w-4 mr-2" />
                  <span>Sent on {new Date().toLocaleDateString()}</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Support Information */}
        <Card>
          <CardHeader>
            <CardTitle>Need Help?</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-3">
                  <span className="text-blue-600 text-xl">💬</span>
                </div>
                <h4 className="font-medium text-gray-900 mb-2">Live Chat</h4>
                <p className="text-sm text-gray-600 mb-3">Available 24/7 for instant help</p>
                <Button variant="outline" size="sm">
                  Start Chat
                </Button>
              </div>
              
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-3">
                  <span className="text-blue-600 text-xl">📧</span>
                </div>
                <h4 className="font-medium text-gray-900 mb-2">Email Support</h4>
                <p className="text-sm text-gray-600 mb-3">support@company.com</p>
                <Button variant="outline" size="sm">
                  Send Email
                </Button>
              </div>
              
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-3">
                  <span className="text-blue-600 text-xl">📞</span>
                </div>
                <h4 className="font-medium text-gray-900 mb-2">Phone Support</h4>
                <p className="text-sm text-gray-600 mb-3">1-800-123-4567</p>
                <Button variant="outline" size="sm">
                  Call Now
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Navigation */}
        <div className="flex justify-center space-x-4">
          <Button variant="outline" onClick={() => navigate('/returns')}>
            Return to Portal
          </Button>
          <Button onClick={() => navigate('/returns/new')}>
            Start Another Return
          </Button>
        </div>
      </div>
    </div>
  );
};

export default ReturnConfirmation;