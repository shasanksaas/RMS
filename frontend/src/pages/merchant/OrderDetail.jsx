import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Package, User, MapPin, CreditCard, Truck, ExternalLink, RefreshCw, Undo2 } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { Alert, AlertDescription } from '../../components/ui/alert';

const OrderDetail = () => {
  const { orderId } = useParams();
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Get backend URL and tenant from environment
  const backendUrl = process.env.REACT_APP_BACKEND_URL;
  const tenantId = 'tenant-fashion-store.myshopify.com'; // TODO: Get from auth context

  useEffect(() => {
    loadOrder();
  }, [orderId]);

  const getApiUrl = () => {
    // Force HTTPS to prevent mixed content issues
    let url = backendUrl;
    if (url && url.startsWith('http://')) {
      url = url.replace('http://', 'https://');
    }
    return url;
  };

  const loadOrder = async () => {
    try {
      setLoading(true);
      setError('');
      
      const apiUrl = getApiUrl();
      let fullUrl = `${apiUrl}/api/orders/${orderId}`;
      
      // Force HTTPS to prevent mixed content errors
      if (fullUrl.startsWith('http://')) {
        fullUrl = fullUrl.replace('http://', 'https://');
      }
      
      const response = await fetch(fullUrl, {
        headers: {
          'Content-Type': 'application/json',
          'X-Tenant-Id': tenantId
        }
      });

      if (response.ok) {
        const orderData = await response.json();
        setOrder(orderData);
      } else if (response.status === 404) {
        setError('Order not found');
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to load order');
      }
    } catch (err) {
      console.error('Error loading order:', err);
      setError('Failed to load order. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status, type = 'financial') => {
    if (type === 'financial') {
      const config = {
        paid: { color: 'bg-green-100 text-green-800', label: 'Paid' },
        pending: { color: 'bg-yellow-100 text-yellow-800', label: 'Pending' },
        cancelled: { color: 'bg-red-100 text-red-800', label: 'Cancelled' },
        refunded: { color: 'bg-purple-100 text-purple-800', label: 'Refunded' }
      };
      const { color, label } = config[status] || { color: 'bg-gray-100 text-gray-800', label: status };
      return <Badge className={color}>{label}</Badge>;
    } else {
      const config = {
        fulfilled: { color: 'bg-green-100 text-green-800', label: 'Fulfilled' },
        unfulfilled: { color: 'bg-yellow-100 text-yellow-800', label: 'Unfulfilled' },
        partial: { color: 'bg-blue-100 text-blue-800', label: 'Partial' },
        cancelled: { color: 'bg-red-100 text-red-800', label: 'Cancelled' }
      };
      const { color, label } = config[status] || { color: 'bg-gray-100 text-gray-800', label: status };
      return <Badge className={color}>{label}</Badge>;
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center space-x-4">
          <Button variant="ghost" asChild className="touch-manipulation">
            <Link to="/app/orders">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Orders
            </Link>
          </Button>
        </div>
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center space-x-4">
          <Button variant="ghost" asChild className="touch-manipulation">
            <Link to="/app/orders">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Orders
            </Link>
          </Button>
        </div>
        <Alert className="border-red-200 bg-red-50">
          <AlertDescription className="text-red-800">
            {error}
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  if (!order) {
    return (
      <div className="space-y-6">
        <div className="flex items-center space-x-4">
          <Button variant="ghost" asChild className="touch-manipulation">
            <Link to="/app/orders">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Orders
            </Link>
          </Button>
        </div>
        <div className="text-center py-12">
          <h3 className="text-lg font-medium text-gray-900">Order not found</h3>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4 md:space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
        <div className="flex items-center space-x-4">
          <Button variant="ghost" asChild className="touch-manipulation">
            <Link to="/app/orders">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Orders
            </Link>
          </Button>
          <div>
            <h1 className="text-2xl md:text-3xl font-bold text-gray-900">Order {order.order_number}</h1>
            <p className="text-gray-500 text-sm md:text-base">
              Placed on {new Date(order.created_at).toLocaleDateString()}
            </p>
          </div>
        </div>
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center space-y-2 sm:space-y-0 sm:space-x-3">
          {order.shopify_order_url && (
            <Button variant="outline" asChild className="touch-manipulation">
              <a href={order.shopify_order_url} target="_blank" rel="noopener noreferrer">
                <ExternalLink className="h-4 w-4 mr-2" />
                View in Shopify
              </a>
            </Button>
          )}
          <Button onClick={loadOrder} className="touch-manipulation">
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Order Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 md:gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2 text-lg">
              <CreditCard className="h-5 w-5" />
              <span>Payment Status</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {getStatusBadge(order.financial_status, 'financial')}
              <div className="text-2xl font-bold">
                ${order.total_price.toFixed(2)} {order.currency_code}
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2 text-lg">
              <Truck className="h-5 w-5" />
              <span>Fulfillment Status</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {getStatusBadge(order.fulfillment_status, 'fulfillment')}
              <div className="text-lg font-medium">
                {order.line_items?.length || 0} items
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2 text-lg">
              <Undo2 className="h-5 w-5" />
              <span>Returns</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="text-lg font-medium">
                {order.returns?.length || 0} returns
              </div>
              {order.returns?.length > 0 && (
                <Button variant="outline" size="sm" asChild className="w-full touch-manipulation">
                  <Link to={`/app/returns?order=${order.order_number}`}>
                    View Returns
                  </Link>
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 md:gap-6">
        {/* Customer Information */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2 text-lg">
              <User className="h-5 w-5" />
              <span>Customer Information</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium text-gray-500">Name</label>
              <div className="text-base">{order.customer_name || 'Unknown'}</div>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-500">Email</label>
              <div className="text-base">{order.customer_email}</div>
            </div>
            {order.customer_id && (
              <div>
                <label className="text-sm font-medium text-gray-500">Customer ID</label>
                <div className="text-sm font-mono">{order.customer_id}</div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Shipping Address */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2 text-lg">
              <MapPin className="h-5 w-5" />
              <span>Shipping Address</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {order.shipping_address ? (
              <div className="space-y-1 text-sm">
                <div>{order.shipping_address.name}</div>
                <div>{order.shipping_address.address1}</div>
                {order.shipping_address.address2 && <div>{order.shipping_address.address2}</div>}
                <div>
                  {order.shipping_address.city}, {order.shipping_address.province} {order.shipping_address.zip}
                </div>
                <div>{order.shipping_address.country}</div>
                {order.shipping_address.phone && <div>Phone: {order.shipping_address.phone}</div>}
              </div>
            ) : (
              <div className="text-gray-500">No shipping address available</div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Line Items */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2 text-lg">
            <Package className="h-5 w-5" />
            <span>Order Items</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {order.line_items && order.line_items.length > 0 ? (
            <div className="space-y-4">
              {order.line_items.map((item, index) => (
                <div key={index} className="flex flex-col sm:flex-row sm:items-center sm:justify-between p-4 border rounded-lg space-y-2 sm:space-y-0">
                  <div className="flex-1">
                    <div className="font-medium">{item.name}</div>
                    {item.sku && <div className="text-sm text-gray-500">SKU: {item.sku}</div>}
                    <div className="text-sm text-gray-500">Quantity: {item.quantity}</div>
                  </div>
                  <div className="text-right">
                    <div className="font-medium">${parseFloat(item.price || 0).toFixed(2)}</div>
                    <div className="text-sm text-gray-500">
                      ${(parseFloat(item.price || 0) * item.quantity).toFixed(2)} total
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <Package className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">No line items available</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Order Timeline */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Order Timeline</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-start space-x-3">
              <div className="w-2 h-2 bg-blue-600 rounded-full mt-2" />
              <div>
                <div className="font-medium">Order Created</div>
                <div className="text-sm text-gray-500">
                  {new Date(order.created_at).toLocaleString()}
                </div>
              </div>
            </div>
            
            {order.processed_at && (
              <div className="flex items-start space-x-3">
                <div className="w-2 h-2 bg-green-600 rounded-full mt-2" />
                <div>
                  <div className="font-medium">Order Processed</div>
                  <div className="text-sm text-gray-500">
                    {new Date(order.processed_at).toLocaleString()}
                  </div>
                </div>
              </div>
            )}

            {order.updated_at && order.updated_at !== order.created_at && (
              <div className="flex items-start space-x-3">
                <div className="w-2 h-2 bg-yellow-600 rounded-full mt-2" />
                <div>
                  <div className="font-medium">Last Updated</div>
                  <div className="text-sm text-gray-500">
                    {new Date(order.updated_at).toLocaleString()}
                  </div>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default OrderDetail;