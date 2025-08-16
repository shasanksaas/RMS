import React, { useState, useEffect } from 'react';
import { Search, ShoppingCart, Package, Loader, AlertCircle, Check } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Alert, AlertDescription } from '../../components/ui/alert';

const ProductSelector = ({ 
  selectedItems, 
  onProductSelect, 
  onVariantSelect, 
  onQuantityChange,
  tenantId,
  showPriceDifference = false
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [error, setError] = useState('');
  const [priceDifference, setPriceDifference] = useState(null);

  // Get backend URL
  const backendUrl = process.env.REACT_APP_BACKEND_URL;

  const searchProducts = async (query) => {
    if (!query || query.length < 2) {
      setProducts([]);
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch(`${backendUrl}/api/exchange/browse-products`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Tenant-Id': tenantId
        },
        body: JSON.stringify({
          query: query,
          limit: 12
        })
      });

      const data = await response.json();

      if (response.ok && data.success) {
        setProducts(data.products || []);
        if (data.products.length === 0) {
          setError('No products found matching your search');
        }
      } else {
        setError(data.message || 'Failed to search products');
        setProducts([]);
      }
    } catch (err) {
      console.error('Product search error:', err);
      setError('Unable to search products. Please try again.');
      setProducts([]);
    } finally {
      setLoading(false);
    }
  };

  const handleProductClick = async (product) => {
    setSelectedProduct(product);
    onProductSelect(product);

    // If product has only one variant, auto-select it
    if (product.variants && product.variants.length === 1) {
      handleVariantSelect(product, product.variants[0]);
    }
  };

  const handleVariantSelect = async (product, variant) => {
    onVariantSelect(product, variant);

    // Calculate price difference if enabled
    if (showPriceDifference && selectedItems && selectedItems.length > 0) {
      await calculatePriceDifference(variant);
    }
  };

  const calculatePriceDifference = async (newVariant) => {
    try {
      const returnedItems = selectedItems.map(item => ({
        price: item.price || item.unit_price || 0,
        quantity: item.quantity || 1
      }));

      const exchangeItems = [{
        variant_id: newVariant.id,
        price: parseFloat(newVariant.price || 0),
        quantity: 1 // Default quantity
      }];

      const response = await fetch(`${backendUrl}/api/exchange/calculate-difference`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Tenant-Id': tenantId
        },
        body: JSON.stringify({
          returned_items: returnedItems,
          exchange_items: exchangeItems
        })
      });

      const data = await response.json();

      if (response.ok && data.success) {
        setPriceDifference(data);
      } else {
        console.error('Price calculation failed:', data);
      }
    } catch (err) {
      console.error('Price calculation error:', err);
    }
  };

  const handleSearchChange = (e) => {
    const query = e.target.value;
    setSearchQuery(query);
    
    // Debounce search
    setTimeout(() => {
      if (query === searchQuery) {
        searchProducts(query);
      }
    }, 500);
  };

  return (
    <div className="space-y-6">
      {/* Search Interface */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Search className="h-5 w-5" />
            <span>Search for Exchange Items</span>
          </CardTitle>
          <CardDescription>
            Find the product you'd like to exchange for
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
            <Input
              type="text"
              placeholder="Search products (e.g., shirt, shoes, jacket)..."
              value={searchQuery}
              onChange={handleSearchChange}
              className="pl-10"
            />
          </div>
          
          {loading && (
            <div className="flex items-center justify-center py-4">
              <Loader className="h-6 w-6 animate-spin text-blue-600" />
              <span className="ml-2">Searching products...</span>
            </div>
          )}

          {error && (
            <Alert variant="destructive" className="mt-4">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Product Results */}
      {products.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Available Products ({products.length})</CardTitle>
            <CardDescription>Click on a product to see available options</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {products.map((product) => (
                <div
                  key={product.id}
                  onClick={() => handleProductClick(product)}
                  className={`border rounded-lg p-4 cursor-pointer transition-all hover:shadow-md ${
                    selectedProduct?.id === product.id 
                      ? 'border-blue-500 bg-blue-50' 
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  {/* Product Image */}
                  <div className="w-full h-32 bg-gray-100 rounded-lg mb-3 flex items-center justify-center overflow-hidden">
                    {product.image_url ? (
                      <img 
                        src={product.image_url} 
                        alt={product.title}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <Package className="h-8 w-8 text-gray-400" />
                    )}
                  </div>

                  {/* Product Info */}
                  <div>
                    <h3 className="font-medium text-sm mb-1 line-clamp-2">{product.title}</h3>
                    <p className="text-xs text-gray-500 mb-2">{product.product_type}</p>
                    
                    {/* Price Range */}
                    {product.variants && product.variants.length > 0 && (
                      <div className="text-sm font-semibold text-green-600">
                        {product.variants.length === 1 
                          ? `$${parseFloat(product.variants[0].price).toFixed(2)}`
                          : `$${Math.min(...product.variants.map(v => parseFloat(v.price))).toFixed(2)} - $${Math.max(...product.variants.map(v => parseFloat(v.price))).toFixed(2)}`
                        }
                      </div>
                    )}

                    {/* Availability */}
                    <div className="mt-2">
                      {product.available ? (
                        <span className="inline-flex items-center text-xs text-green-600">
                          <Check className="h-3 w-3 mr-1" />
                          Available
                        </span>
                      ) : (
                        <span className="text-xs text-red-500">Out of Stock</span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Variant Selection */}
      {selectedProduct && selectedProduct.variants && selectedProduct.variants.length > 1 && (
        <Card>
          <CardHeader>
            <CardTitle>Choose Your Option</CardTitle>
            <CardDescription>Select size, color, or other options for {selectedProduct.title}</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {selectedProduct.variants
                .filter(variant => variant.available && variant.inventory_quantity > 0)
                .map((variant) => (
                <div
                  key={variant.id}
                  onClick={() => handleVariantSelect(selectedProduct, variant)}
                  className="border rounded-lg p-4 cursor-pointer transition-all hover:shadow-sm hover:border-gray-300 hover:bg-gray-50"
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <h4 className="font-medium">{variant.title}</h4>
                      {variant.sku && (
                        <p className="text-sm text-gray-500">SKU: {variant.sku}</p>
                      )}
                      <p className="text-sm text-gray-600 mt-1">
                        {variant.inventory_quantity} in stock
                      </p>
                    </div>
                    <div className="text-right">
                      <div className="font-semibold text-green-600">
                        ${parseFloat(variant.price).toFixed(2)}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Price Difference Display */}
      {priceDifference && (
        <Card className="border-orange-200 bg-orange-50">
          <CardHeader>
            <CardTitle className="text-orange-900">Price Difference</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span>Items being returned:</span>
                <span className="font-medium">${priceDifference.returned_total.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span>New item cost:</span>
                <span className="font-medium">${priceDifference.exchange_total.toFixed(2)}</span>
              </div>
              <hr className="border-orange-200" />
              <div className="flex justify-between font-semibold">
                <span>
                  {priceDifference.difference_type === 'charge' ? 'You pay:' 
                   : priceDifference.difference_type === 'refund' ? 'You get back:' 
                   : 'No difference'}
                </span>
                <span className={
                  priceDifference.difference_type === 'charge' ? 'text-red-600' 
                  : priceDifference.difference_type === 'refund' ? 'text-green-600' 
                  : 'text-gray-600'
                }>
                  {priceDifference.difference_type === 'even' 
                    ? '$0.00' 
                    : `$${priceDifference.absolute_difference.toFixed(2)}`
                  }
                </span>
              </div>
              
              {priceDifference.difference_type === 'charge' && (
                <Alert>
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    You'll be charged the difference when we process your exchange.
                  </AlertDescription>
                </Alert>
              )}
              
              {priceDifference.difference_type === 'refund' && (
                <Alert>
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    We'll refund the difference to your original payment method.
                  </AlertDescription>
                </Alert>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Helpful Tips */}
      <Card className="bg-blue-50 border-blue-200">
        <CardContent className="p-4">
          <div className="flex items-start space-x-3">
            <AlertCircle className="h-5 w-5 text-blue-600 mt-0.5 flex-shrink-0" />
            <div className="text-sm text-blue-800">
              <p className="font-medium mb-1">Exchange Tips:</p>
              <ul className="space-y-1 text-blue-700">
                <li>• Search by product name, type, or brand</li>
                <li>• You can exchange for a different product entirely</li>
                <li>• Price differences will be calculated automatically</li>
                <li>• New items ship after we receive your return</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ProductSelector;