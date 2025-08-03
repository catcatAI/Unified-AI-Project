import { render, screen } from '@testing-library/react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './tabs';

describe('Tabs', () => {
  it('renders a set of tabs', () => {
    render(
      <Tabs defaultValue="account">
        <TabsList>
          <TabsTrigger value="account">Account</TabsTrigger>
          <TabsTrigger value="password">Password</TabsTrigger>
        </TabsList>
        <TabsContent value="account">
          <p>Account content</p>
        </TabsContent>
        <TabsContent value="password">
          <p>Password content</p>
        </TabsContent>
      </Tabs>
    );
    expect(screen.getByText('Account')).toBeInTheDocument();
    expect(screen.getByText('Password')).toBeInTheDocument();
    expect(screen.getByText('Account content')).toBeInTheDocument();
  });
});
