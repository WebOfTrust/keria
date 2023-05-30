import React, { useEffect, useState } from 'react';
import {
  AppBar,
  Paper,
  Toolbar,
  DialogTitle,
  DialogContentText,
  DialogContent,
  DialogActions,
  IconButton,
  Typography,
  Button,
  Dialog,
  List,
  ListItem,
  ListItemText,
  Drawer,
  TextField,
  Autocomplete,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Divider, Grid, Stack, Box
} from '@mui/material';
import { Circle, Menu, Rectangle } from '@mui/icons-material';
import { max } from 'lodash';
import { SignifyClient } from 'signify-ts';

const tableObject = {
  v: {
    title: "Version String",
    description: "",
    notes: ""
  },
  i: {
    title: "Identifier Prefix (AID)",
    description: "",
    notes: ""
  },
  s: {
    title: "Sequence Number",
    description: "",
    notes: ""
  },
  t: {
    title: "Message Type",
    description: "",
    notes: ""
  },
  te: {
    title: "Last received Event Message Type in a Key State Notice",
    description: "",
    notes: ""
  },
  d: {
    title: "Event SAID",
    description: "",
    notes: ""
  },
  p: {
    title: "Prior Event SAID",
    description: "",
    notes: ""
  },
  kt: {
    title: "Keys Signing Threshold",
    description: "",
    notes: ""
  },
  k: {
    title: "List of Signing Keys (ordered key set)",
    description: "",
    notes: ""
  },
  nt: {
    title: "Next Keys Signing Threshold",
    description: "",
    notes: ""
  },
  n: {
    title: "List of Next Key Digests (ordered key digest set)",
    description: "",
    notes: ""
  },
  bt: {
    title: "Backer Threshold",
    description: "",
    notes: ""
  },
  b: {
    title: "List of Backers (ordered backer set of AIDs)",
    description: "",
    notes: ""
  },
  br: {
    title: "List of Backers to Remove (ordered backer set of AIDs)",
    description: "",
    notes: ""
  },
  ba: {
    title: "List of Backers to Add (ordered backer set of AIDs)",
    description: "",
    notes: ""
  },
  c: {
    title: "List of Configuration Traits/Modes",
    description: "",
    notes: ""
  },
  a: {
    title: "List of Anchors (seals)",
    description: "",
    notes: ""
  },
  di: {
    title: "Delegator Identifier Prefix (AID)",
    description: "",
    notes: ""
  },
  rd: {
    title: "Merkle Tree Root Digest (SAID)",
    description: "",
    notes: ""
  },
  ee: {
    title: "Last Establishment Event Map",
    description: "",
    notes: ""
  },
  vn: {
    title: "Version Number ('major.minor')",
    description: "",
    notes: ""
  }
};

const MainComponent = () => {
  const [selectedComponent, setSelectedComponent] = useState(null);
  const [client, setClient] = useState(null); // [pre, icp, key
  const [open, setOpen] = useState(true);
  const [drawerOpen, setDrawerOpen] = useState(false); // Open drawer by default
  const [url, setUrl] = useState('');
  const [passcode, setPasscode] = useState('');
  const [status, setStatus] = useState('Not Connected');

  const toggleDrawer = (open) => (event) => {
    if (event.type === 'keydown' && (event.key === 'Tab' || event.key === 'Shift')) {
      return;
    }
    setDrawerOpen(open);
  };

  const handleClickOpen = () => {
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
  };

  const renderComponent = (componentName) => {
    setSelectedComponent(componentName);
  };

  return (
    <div>
      <AppBar position="fixed" sx={{ width: '100%' }}>
        <Toolbar sx={{
          display: 'flex',
          justifyContent: 'space-between',
        }}>
          <IconButton edge="start" color="inherit" aria-label="menu" onClick={toggleDrawer(!drawerOpen)}>
            <Menu />
          </IconButton>
          <Typography variant="h6">
            Signify Client
          </Typography>
          <Button color="inherit" sx={{ marginLeft: 'auto' }} onClick={handleClickOpen}>
            <Circle sx={{
              color: status === 'Not Connected' ? 'red' : 'green'
            }} />
            Connect
          </Button>
        </Toolbar>
      </AppBar>

      <Drawer open={drawerOpen} onClose={toggleDrawer(false)}>
        <div
          width='250px'
          role="presentation"
          onClick={toggleDrawer(false)}
          onKeyDown={toggleDrawer(false)}
        >
          <List>
            {['Identifiers', 'Credentials', 'Client'].map((text, index) => (
              <ListItem button key={text} onClick={() => renderComponent(text)}>
                <ListItemText primary={text} />
              </ListItem>
            ))}
          </List>
        </div>
      </Drawer>

      <Dialog open={open} onClose={handleClose}>
        <DialogTitle>Connect</DialogTitle>
        <DialogContent>
          <Stack spacing={3}>
            <Autocomplete
              id="combo-box-demo"
              options={['https://keria-dev.rootsid.cloud', 'http://localhost:3901']}
              renderInput={(params) => (
                <TextField
                  {...params}
                  fullWidth
                />
              )}
              sx={{ width: 300 }}
              value={url}
              fullWidth
              onChange={(event, newValue) => {
                setUrl(newValue);
              }}

            />
            <Stack direction="row" spacing={2}>

              <TextField
                id="outlined-password-input"
                label="Passcode"
                type="text"
                autoComplete="current-password"
                variant="outlined"

                value={passcode}
                onChange={(e) => setPasscode(e.target.value)}
                helperText="Passcode must be at least 21 characters"
              />
              <Button variant="contained" color="primary" onClick={() => setPasscode('0123456789abcdefghijk')} sx={{
                padding: '4px',
                height: '40px',
                marginTop: '10px'
              }} >
                Create
              </Button>
            </Stack>

            <Button variant="contained" color="primary" onClick={
              () => {
                const client = new SignifyClient(url, passcode);
                console.log(client.controller.pre)
                setClient(client)
                return setStatus('Connected')
              }
            }>
              Connect
            </Button>
          </Stack>
        </DialogContent>
        <Box mt={2}>
          <Divider />
        </Box>
        <DialogActions>
          <Grid container justify="center" spacing={2}>
            <Grid item xs={12}>
              <Button fullWidth disabled
                sx={{
                  "&.Mui-disabled": {
                    background: status === 'Not Connected' ? 'red' : 'green',
                    color: "black"
                  }
                }}>
                Status: {status}
              </Button>
            </Grid>
            {status === 'Connected' &&
              <Grid item xs={12}>
                <Typography sx={{ maxWidth: '120px' }}>AID: {client.controller.pre.slice(0, 5)}....{client.controller.pre.slice(client.controller.pre.length - 5, client.controller.pre.length)}
                </Typography>
              </Grid>}

            <Grid item xs={12}>
              <Button onClick={handleClose} color='primary' fullWidth>
                Close
              </Button>
            </Grid>
          </Grid>
        </DialogActions>
      </Dialog>
      {selectedComponent === 'Identifiers' && <IdentifiersComponent client={client.identifiers()} />}
      {selectedComponent === 'Credentials' && <CredentialsComponent />}
      {selectedComponent === 'Client' && <ClientComponent client={client} />}
    </div>
  );
};
const IdentifiersComponent = ({ client }) => {
  const [identifiers, setIdentifiers] = useState(null)
  //async useeffect
  useEffect(() => {
    const getIdentifiers = async () => {
      setIdentifiers(null)
      const list_identifiers = await client.list_identifiers()
      setIdentifiers(list_identifiers)
      console.log(list_identifiers)
    }
    getIdentifiers()
  }, [])

  const handleClick = async (aid: string) => {
    // Your asynchronous function logic here
    await client.rotate(aid,{})
  };

  //render the identifiers
  if (!identifiers) return <div>Loading...</div>
  const data = JSON.stringify(identifiers, null, 2)


  return <>
    <Button variant="contained" color="primary"
      onClick={async () => {
        const length = identifiers.length.toString()
        await client.create(`aid${length}`, {})
        const list_identifiers = await client.list_identifiers()
        setIdentifiers(list_identifiers)
      }
      }
      sx={{
        padding: '4px',
        height: '40px',
        marginTop: '10px'
      }} >
      Create Identifier
    </Button>

    <TableContainer component={Paper}>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Name</TableCell>
            <TableCell>Action</TableCell>
            <TableCell>Prefix</TableCell>
            <TableCell>Salty sxlt</TableCell>
            <TableCell>Salty pidx</TableCell>
            <TableCell>Salty kidx</TableCell>
            <TableCell>Salty stem</TableCell>
            <TableCell>Salty tier</TableCell>
            <TableCell>Salty dcode</TableCell>
            <TableCell>Salty icodes</TableCell>
            <TableCell>Salty ncodes</TableCell>
            <TableCell>Transferable</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {identifiers.map((item, index) => (
            <TableRow key={index}>
              <TableCell>{item.name}</TableCell>
              <TableCell>
              <Button onClick={() => handleClick(item.name)}>Rotate</Button>
              </TableCell>
              <TableCell>{item.prefix.slice(0,10)}...{item.prefix.slice(item.prefix.length-10,item.prefix.length)}</TableCell>
              <TableCell>{item.salty.sxlt.slice(0,10)}....</TableCell>
              <TableCell>{item.salty.pidx}</TableCell>
              <TableCell>{item.salty.kidx}</TableCell>
              <TableCell>{item.salty.stem}</TableCell>
              <TableCell>{item.salty.tier}</TableCell>
              <TableCell>{item.salty.dcode}</TableCell>
              <TableCell>{item.salty.icodes.join(', ')}</TableCell>
              <TableCell>{item.salty.ncodes.join(', ')}</TableCell>
              <TableCell>{item.salty.transferable.toString()}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
    {/* <pre> {data}</pre> */}


    <Button variant="contained" color="primary"

      //async onclick
      onClick={async () => {
        const list_identifiers = await client.list_identifiers()
        setIdentifiers(list_identifiers)
      }
      }

      sx={{
        padding: '4px',
        height: '40px',
        marginTop: '10px'
      }} >
      Update
    </Button>


  </>



};
//make it component 
const CredentialsComponent = () => <div>Credentials Component</div>;

const ClientComponent = ({ client }) => {
  //write an async function to get the client in the client component
  const [controller, setController] = useState(null)
  const [agent, setAgent] = useState(null)
  useEffect(() => {
    const getController = async () => {
      try {
        await client.connect()
        const controller = await client.state();
        setAgent(controller.agent)
        setController(controller.controller.state)
        console.log(JSON.stringify(controller.controller, null, 2))

      } catch (e) {
        console.log('controller not found')
        await client.boot();
        await client.connect()
        const controller = await client.state();
        setAgent(controller.agent)
        setController(controller.controller.state)
        console.log(JSON.stringify(controller, null, 2))
      }
    }
    getController();
  }
    , [client])
  return (
    agent !== null ? 
      <>
        <Card>
          <CardContent>
            <Typography variant="h6" component="div" gutterBottom>
              Agent
            </Typography>
            <Divider />
            <Grid container spacing={2}>
              {Object.entries(agent).map(([key, value]) =>
                typeof value === 'string' ? (
                  <Grid item xs={12} sm={6} md={4} lg={3} key={key}>
                    <Typography variant="subtitle1" gutterBottom>
                      <strong>{key}</strong>
                    </Typography>
                    <Typography variant="body1">{value}</Typography>
                  </Grid>
                ) : null
              )}
            </Grid>
          </CardContent>
        </Card>

        <Card>
          <CardContent>
            <Typography variant="h6" component="div" gutterBottom>
              Controller
            </Typography>
            <Divider />
            <Grid container spacing={2}>
              {Object.entries(controller).map(([key, value]) =>
                typeof value === 'string' ? (
                  <Grid item xs={12} sm={6} md={4} lg={3} key={key}>
                    <Typography variant="subtitle1" gutterBottom>
                      <strong>{key}</strong>
                    </Typography>
                    <Typography variant="body1">{value}</Typography>
                  </Grid>
                ) : null
              )}
            </Grid>
          </CardContent>
        </Card>
        <Divider />
        <Button variant="contained" color="primary" onClick={() => console.log('rotate')}>
          Rotate
        </Button>
      </>
      : <div>loading...</div>
  );

};

export default MainComponent;
