import React, { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, Package, DollarSign, RefreshCw, Calendar } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';

const Dashboard = () => {
  const [timeframe, setTimeframe] = useState('7d');
  const [loading, setLoading] = useState(false);
  const [kpis, setKpis] = useState({
    totalReturns: 45,
    returnRate: 12.3,
    exchangeRate: 34.2,
    avgResolutionTime: 2.4,
    revenueSaved: 15420,
    topReasons: [
      { reason: 'Wrong size', count: 18, percentage: 40 },
      { reason: 'Defective', count: 12, percentage: 27 },
      { reason: 'Wrong color', count: 8, percentage: 18 },
      { reason: 'Not as described', count: 7, percentage: 15 }
    ]
  });

  const refreshData = async () => {
    setLoading(true);
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000));
    setLoading(false);
  };

  return (
    <div className="space-y-4 md:space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-500 text-sm md:text-base">Returns management overview</p>
        </div>
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center space-y-3 sm:space-y-0 sm:space-x-3">
          <Select value={timeframe} onValueChange={setTimeframe}>
            <SelectTrigger className="w-full sm:w-36">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="7d">Last 7 days</SelectItem>
              <SelectItem value="30d">Last 30 days</SelectItem>
              <SelectItem value="90d">Last 90 days</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline" onClick={refreshData} disabled={loading} className="w-full sm:w-auto">
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 md:gap-6">
        <Card className="hover:shadow-md transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Returns</CardTitle>
            <Package className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-xl md:text-2xl font-bold">{kpis.totalReturns}</div>
            <p className="text-xs text-muted-foreground flex items-center">
              <TrendingUp className="h-3 w-3 inline mr-1" />
              +12% from last period
            </p>
          </CardContent>
        </Card>

        <Card className="hover:shadow-md transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Return Rate</CardTitle>
            <TrendingDown className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-xl md:text-2xl font-bold">{kpis.returnRate}%</div>
            <p className="text-xs text-muted-foreground flex items-center">
              <TrendingDown className="h-3 w-3 inline mr-1" />
              -2.1% from last period
            </p>
          </CardContent>
        </Card>

        <Card className="hover:shadow-md transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Exchange Rate</CardTitle>
            <RefreshCw className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-xl md:text-2xl font-bold">{kpis.exchangeRate}%</div>
            <p className="text-xs text-muted-foreground flex items-center">
              <TrendingUp className="h-3 w-3 inline mr-1" />
              +5.3% from last period
            </p>
          </CardContent>
        </Card>

        <Card className="hover:shadow-md transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Resolution Time</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-xl md:text-2xl font-bold">{kpis.avgResolutionTime} days</div>
            <p className="text-xs text-muted-foreground flex items-center">
              <TrendingDown className="h-3 w-3 inline mr-1" />
              -0.8 days from last period
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 md:gap-6">
        {/* Revenue Impact */}
        <Card className="hover:shadow-md transition-shadow">
          <CardHeader>
            <CardTitle className="text-lg">Revenue Saved</CardTitle>
            <CardDescription className="text-sm">
              Revenue retained through exchanges and store credit
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl md:text-3xl font-bold text-green-600">
              ${kpis.revenueSaved.toLocaleString()}
            </div>
            <div className="mt-4 space-y-2">
              <div className="flex justify-between text-sm">
                <span>Exchanges</span>
                <span className="font-medium">$8,240</span>
              </div>
              <div className="flex justify-between text-sm">
                <span>Store Credit</span>
                <span className="font-medium">$7,180</span>
              </div>
              <div className="border-t pt-2 flex justify-between font-medium">
                <span>Total Saved</span>
                <span>${kpis.revenueSaved.toLocaleString()}</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Top Return Reasons */}
        <Card className="hover:shadow-md transition-shadow">
          <CardHeader>
            <CardTitle className="text-lg">Top Return Reasons</CardTitle>
            <CardDescription className="text-sm">
              Most common reasons for returns
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {kpis.topReasons.map((reason, index) => (
                <div key={index} className="flex items-center space-x-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex justify-between text-sm mb-1">
                      <span className="font-medium truncate">{reason.reason}</span>
                      <span className="text-gray-500 ml-2 flex-shrink-0">{reason.count} returns</span>
                    </div>
                    <div className="bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${reason.percentage}%` }}
                      />
                    </div>
                  </div>
                  <span className="text-sm font-medium ml-2 flex-shrink-0">{reason.percentage}%</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Activity */}
      <Card className="hover:shadow-md transition-shadow">
        <CardHeader>
          <CardTitle className="text-lg">Recent Activity</CardTitle>
          <CardDescription className="text-sm">Latest return requests and updates</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3 md:space-y-4">
            {[
              {
                id: 'RET-001',
                customer: 'Sarah Johnson',
                action: 'Created return request',
                product: 'Blue Cotton T-Shirt',
                status: 'pending',
                time: '2 minutes ago'
              },
              {
                id: 'RET-002', 
                customer: 'Mike Chen',
                action: 'Return approved',
                product: 'Wireless Headphones',
                status: 'approved',
                time: '15 minutes ago'
              },
              {
                id: 'RET-003',
                customer: 'Emma Davis',
                action: 'Return resolved - refunded',
                product: 'Summer Dress',
                status: 'resolved',
                time: '1 hour ago'
              }
            ].map((activity) => (
              <div key={activity.id} className="flex flex-col sm:flex-row sm:items-center space-y-2 sm:space-y-0 sm:space-x-4 p-3 border rounded-lg hover:bg-gray-50 transition-colors">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{activity.customer}</p>
                  <p className="text-sm text-gray-500">{activity.action}</p>
                  <p className="text-xs text-gray-400">{activity.product} • {activity.time}</p>
                </div>
                <div className="flex-shrink-0">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    activity.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                    activity.status === 'approved' ? 'bg-blue-100 text-blue-800' :
                    'bg-green-100 text-green-800'
                  }`}>
                    {activity.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Dashboard;