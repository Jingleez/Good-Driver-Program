// src/components/Header.js
import React from 'react';
import { AppBar, Toolbar, Typography, Button } from '@mui/material';

const Header = () => {
  return (
    <AppBar position="static" color="primary">
      <Toolbar>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          Driver Dashboard
        </Typography>
        <Button color="inherit" href="/profile">Profile</Button>
        <Button color="inherit" href="/points">Points</Button>
        <Button color="inherit" href="/catalog">Catalog</Button>
        <Button color="inherit" href="/purchases">Purchases</Button>
        <Button color="inherit" href="/trips">Trips</Button>
        <Button color="inherit" href="/logout">Logout</Button>
      </Toolbar>
    </AppBar>
  );
}

export default Header;
