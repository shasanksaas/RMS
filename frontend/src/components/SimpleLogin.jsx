import React from 'react';

const SimpleLogin = () => {
  const handleDirectLogin = async () => {
    try {
      console.log('🚀 Starting direct login...');
      
      const response = await fetch('https://ecom-return-manager.preview.emergentagent.com/api/users/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Tenant-Id': 'tenant-rms34'
        },
        body: JSON.stringify({
          tenant_id: 'tenant-rms34',
          email: 'merchant@test.com',
          password: 'MerchantPass123!',
          remember_me: false
        })
      });
      
      console.log('Response status:', response.status);
      
      if (response.ok) {
        const data = await response.json();
        console.log('Login success:', data);
        
        // Store auth data
        localStorage.setItem('auth_token', data.access_token);
        localStorage.setItem('currentTenant', 'tenant-rms34');
        localStorage.setItem('user_info', JSON.stringify(data.user));
        
        // Force redirect
        window.location.href = data.user.role === 'admin' ? '/admin/tenants' : '/app/dashboard';
        
      } else {
        const error = await response.json();
        console.error('Login failed:', error);
        alert('Login failed: ' + (error.detail || 'Unknown error'));
      }
      
    } catch (error) {
      console.error('Network error:', error);
      alert('Network error: ' + error.message);
    }
  };
  
  const handleAdminLogin = async () => {
    try {
      const response = await fetch('https://ecom-return-manager.preview.emergentagent.com/api/users/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Tenant-Id': 'tenant-rms34'
        },
        body: JSON.stringify({
          tenant_id: 'tenant-rms34',
          email: 'admin@returns-manager.com',
          password: 'AdminPassword123!',
          remember_me: false
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('auth_token', data.access_token);
        localStorage.setItem('currentTenant', 'tenant-rms34');
        localStorage.setItem('user_info', JSON.stringify(data.user));
        window.location.href = '/admin/tenants';
      } else {
        const error = await response.json();
        alert('Admin login failed: ' + (error.detail || 'Unknown error'));
      }
    } catch (error) {
      alert('Network error: ' + error.message);
    }
  };

  return (
    <div style={{ 
      maxWidth: '400px', 
      margin: '100px auto', 
      padding: '30px', 
      border: '1px solid #ddd', 
      borderRadius: '8px',
      fontFamily: 'Arial, sans-serif'
    }}>
      <h2 style={{ textAlign: 'center', marginBottom: '30px' }}>🚀 Direct Login Test</h2>
      
      <button
        onClick={handleDirectLogin}
        style={{
          width: '100%',
          padding: '15px',
          backgroundColor: '#007cba',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          fontSize: '16px',
          cursor: 'pointer',
          marginBottom: '10px'
        }}
      >
        🏪 Login as Merchant
      </button>
      
      <button
        onClick={handleAdminLogin}
        style={{
          width: '100%',
          padding: '15px',
          backgroundColor: '#28a745',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          fontSize: '16px',
          cursor: 'pointer',
          marginBottom: '20px'
        }}
      >
        👤 Login as Admin
      </button>
      
      <div style={{ 
        fontSize: '12px', 
        color: '#666', 
        textAlign: 'center',
        marginTop: '20px'
      }}>
        <p><strong>Merchant:</strong> merchant@test.com / MerchantPass123!</p>
        <p><strong>Admin:</strong> admin@returns-manager.com / AdminPassword123!</p>
        <p><strong>Tenant:</strong> tenant-rms34</p>
      </div>
      
      <div style={{ 
        fontSize: '12px', 
        color: '#999', 
        textAlign: 'center',
        marginTop: '10px'
      }}>
        This bypasses all React complexity and just does direct API calls.
      </div>
    </div>
  );
};

export default SimpleLogin;