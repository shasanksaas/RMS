import React, { useState } from 'react';
import RulesList from '../../components/rules/RulesList';
import RuleBuilder from '../../components/rules/RuleBuilder';

const Rules = () => {
  const [showRuleBuilder, setShowRuleBuilder] = useState(false);
  const [editingRule, setEditingRule] = useState(null);

  const handleCreateRule = () => {
    setEditingRule(null);
    setShowRuleBuilder(true);
  };

  const handleEditRule = (rule) => {
    setEditingRule(rule);
    setShowRuleBuilder(true);
  };

  const handleSaveRule = async (ruleData) => {
    try {
      const url = editingRule 
        ? `${process.env.REACT_APP_BACKEND_URL}/api/rules/${editingRule.id}`
        : `${process.env.REACT_APP_BACKEND_URL}/api/rules`;
      
      const method = editingRule ? 'PUT' : 'POST';
      
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'X-Tenant-Id': localStorage.getItem('currentTenant') || 'tenant-fashion-store'
        },
        body: JSON.stringify(ruleData)
      });

      if (!response.ok) {
        throw new Error('Failed to save rule');
      }

      setShowRuleBuilder(false);
      setEditingRule(null);
      
      // Trigger refresh of rules list
      window.location.reload();
    } catch (error) {
      console.error('Error saving rule:', error);
      throw error;
    }
  };

  const handleDeleteRule = (ruleId) => {
    // Handle delete if needed
    console.log('Rule deleted:', ruleId);
  };

  const handleCancel = () => {
    setShowRuleBuilder(false);
    setEditingRule(null);
  };

  return (
    <>
      <RulesList
        onCreateRule={handleCreateRule}
        onEditRule={handleEditRule}
        onDeleteRule={handleDeleteRule}
      />
      
      <RuleBuilder
        rule={editingRule}
        isOpen={showRuleBuilder}
        onSave={handleSaveRule}
        onCancel={handleCancel}
      />
    </>
  );
};

export default Rules;