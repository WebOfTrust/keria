// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore
import { SignifyClient, Identifier} from 'signify-ts';
import  { SetStateAction, useEffect, useState } from 'react';
import {
  AppBar,
  Paper,
  Toolbar,
  DialogTitle,
  DialogContent,
  Modal,
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
  Fab,
  Divider, Grid, Stack, Box,
  FormControl, Select, InputLabel, MenuItem
} from '@mui/material';
import { Circle, Delete, Menu } from '@mui/icons-material';
import AddIcon from '@mui/icons-material/Add';
import { TestsComponent } from './TestsComponent';



const tableObject:any = {
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
  et: {
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
  },
  dt: {
    title: "Datetime of the SAID",
    description: "",
    notes: ""
  },
  f: {
    title: "Number of first seen ordinal",
    description: "",
    notes: ""
  }
};

const MainComponent = () => {
  const [selectedComponent, setSelectedComponent] = useState(null);
  const [client, setClient] = useState<SignifyClient|null>(null); 
  const [open, setOpen] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false); // Open drawer by default
  const [url, setUrl] = useState('');
  const [passcode, setPasscode] = useState('');
  const [status, setStatus] = useState('Not Connected');

  const toggleDrawer = (open:boolean) => (event:any) => {
    if (event.type === 'keydown' && (event.key === 'Tab' || event.key === 'Shift')) {
      return;
    }
    console.log('menu')
    setDrawerOpen(open);
  };

  const handleClickOpen = () => {
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
  };

  const renderComponent = (componentName: SetStateAction<any>) => {
    setSelectedComponent(componentName);
  };

  const connectToAgent = async (client: SignifyClient) => {
    try {
      await client.connect()
      const controller = await client.state();
      console.log(JSON.stringify(controller.controller, null, 2))

    } catch (e) {
      console.log('controller not found')
      await client.boot();
      await client.connect()
      const controller = await client.state();
      console.log(JSON.stringify(controller, null, 2))
    }
  }
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
          // width='250px'
          role="presentation"
          onClick={toggleDrawer(false)}
          onKeyDown={toggleDrawer(false)}
        >
          <List>
            {['Identifiers', 'Credentials', 'Client', 'Tests'].map((text) => (
              <ListItem key={text} onClick={() => renderComponent(text)}>
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
              onChange={(_event, newValue) => {
                setUrl(newValue!);
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
                connectToAgent(client)
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
          <Grid container spacing={2}>
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

            <Grid item xs={12}>
              <Button onClick={handleClose} color='primary' fullWidth>
                Close
              </Button>
            </Grid>
          </Grid>
        </DialogActions>
      </Dialog>
      {selectedComponent === 'Identifiers' && <IdentifierTable client={client!.identifiers()} />}

      {selectedComponent === 'Credentials' && <CredentialsComponent />}
      {selectedComponent === 'Client' && <ClientComponent client={client} />}
      {selectedComponent === 'Tests' && <TestsComponent />}
    </div>
  );
};

({ client }: { client:Identifier}) => {
  const [identifiers, setIdentifiers] = useState<any[]>([])
  //async useeffect
  const getIdentifiers = async () => {
    const list_identifiers = await client.list()
    setIdentifiers(list_identifiers)
    console.log(list_identifiers)
  }
  useEffect(() => {

    getIdentifiers()
  }, [])

  const handleClick = async (aid: string) => {
    // Your asynchronous function logic here
    await client.rotate(aid, {})
    await getIdentifiers()
  };

  //render the identifiers
  if (!identifiers) return <div>Loading...</div>
  // const data = JSON.stringify(identifiers, null, 2)


  return <>
    <Box position='relative'>
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
                <TableCell>{item.prefix.slice(0, 10)}...{item.prefix.slice(item.prefix.length - 10, item.prefix.length)}</TableCell>
                <TableCell>{item.salty.sxlt.slice(0, 10)}....</TableCell>
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
      <Fab
        color="primary"
        aria-label="add"
        style={{ position: 'fixed', bottom: '20px', right: '20px' }}
        onClick={async () => {
          const length = identifiers.length.toString()
          await client.create(`aid${length}`)
          const list_identifiers = await client.list()
          setIdentifiers(list_identifiers)
        }}
      >
        <AddIcon />
      </Fab>

    </Box>
  </>



};
(identifierType:any, data:any) => {
  switch (identifierType) {
    case 'randy':
      return (
        <>
          <Typography variant="h6">PRXS:</Typography>
          {data.prxs.map((prx:string, index:string) => <Typography key={index}>{prx}</Typography>)}
          <Typography variant="h6">NXTS:</Typography>
          {data.nxts.map((nxt:string, index:string) => <Typography key={index}>{nxt}</Typography>)}
        </>
      );
    case 'salty':
      return (
        <>
          <Typography variant="h6">SXLT: {data.sxlt}</Typography>
          <Typography variant="h6">PIDX: {data.pidx}</Typography>
          <Typography variant="h6">KIDX: {data.kidx}</Typography>
          <Typography variant="h6">Stem: {data.stem}</Typography>
          <Typography variant="h6">Tier: {data.tier}</Typography>
          <Typography variant="h6">DCode: {data.dcode}</Typography>
          <Typography variant="h6">ICodes:</Typography>
          {data.icodes.map((icode:string, index:string) => <Typography key={index}>{icode}</Typography>)}
          <Typography variant="h6">NCodes:</Typography>
          {data.ncodes.map((ncode:string, index:string) => <Typography key={index}>{ncode}</Typography>)}
          <Typography variant="h6">Transferable: {data.transferable ? 'Yes' : 'No'}</Typography>
        </>
      );
    default:
      return null;
  }
};

const IdentifierTable = ({ client }:{client:Identifier}) => {
  const [open, setOpen] = useState(false);
  const [currentIdentifier, setCurrentIdentifier] = useState<any>({});
  const [identifiers, setIdentifiers] = useState([])

  const [openCreate, setOpenCreate] = useState(false);
  const [type, setType] = useState('salty');
  const [name, setName] = useState('');
  const [dynamicFields, setDynamicFields] = useState<any[]>([]);
  const [dynamicFieldsValues, setDynamicFieldsValues] = useState<any[]>([]);
  const [selectedField, setSelectedField] = useState('');
  //async useeffect
  const getIdentifiers = async () => {
    const list_identifiers = await client.list()
    setIdentifiers(list_identifiers)
    console.log(list_identifiers)
  }
  useEffect(() => {

    getIdentifiers()
  }, [])
  const handleOpen = (identifier:any) => {
    setCurrentIdentifier(identifier);
    setOpen(true);
  };

  const handleClickRotate = async (aid: string) => {
    // Your asynchronous function logic here
    await client.rotate(aid, {})
    await getIdentifiers()
  };

  const handleClose = () => {
    setOpen(false);
  };

  const body = (
    <Box sx={{
      position: 'absolute',
      top: '50%',
      left: '50%',
      transform: 'translate(-50%, -50%)',
      width: 400,
      bgcolor: 'background.paper',
      boxShadow: 24, p: 4,
      overflow: 'auto',
      maxHeight: '80vh',
    }}>
      <h2>Identifier Details</h2>
      <p>Name: {currentIdentifier.name}</p>
      <p>Prefix: {currentIdentifier.prefix}</p>
      <p>Type: {Object.keys(currentIdentifier)[2]}</p>

      {/* {  getTypeDetails(
    Object.keys(currentIdentifier)[2],currentIdentifier[Object.keys(currentIdentifier)[2]]
    )} */}

      <pre>{JSON.stringify(currentIdentifier[Object.keys(currentIdentifier)[2]], null, 2)}</pre>
      <Button onClick={() => handleClickRotate(currentIdentifier.name)}>Rotate</Button>
    </Box>
  );

  const handleOpenCreate = () => {
    setOpenCreate(true);
  };

  const handleCloseCreate = () => {
    setOpenCreate(false);
  };

  const handleComplete = async () => {
    console.log('Type:', type);
    console.log('Name:', name);
    console.log('Dynamic Fields:', dynamicFields);
    console.log('Dynamic Fields Values:', dynamicFieldsValues);
    
    let fields:any = {
      algo: type,
    }
    dynamicFields.forEach((field, index) => {
      if (field == 'count' || field =='ncount' ){
        fields[field] = parseInt(dynamicFieldsValues[index]);
      }
      else if (field == 'transferable'){
        fields[field] = dynamicFieldsValues[index] == 'true' ? true : false;
      }
      else if (field == 'icodes' || field == 'ncodes' || field == 'prxs' || field == 'nxts'|| field == 'cuts' || field == 'adds'){
        fields[field] = dynamicFieldsValues[index].split(',');
      }
      else {
      fields[field] = dynamicFieldsValues[index];
      }
    });
    console.log('name:', name);

    console.log('Fields:', fields);

    //create identifier
    client.create(name, fields)
    const list_identifiers = await client.list()
    setIdentifiers(list_identifiers)
    handleClose();
  };

  const handleTypeChange = (event:any) => {
    setType(event.target.value);
  };

  const handleFieldChange = (event:any) => {
    const prevFields:any[] = [...dynamicFields];
    //add field to array
    prevFields.push(event.target.value);
    setSelectedField(event.target.value);
    setDynamicFields(prevFields);

    const prevFieldsValues:any[] = [...dynamicFieldsValues];
    //add field to array
    prevFieldsValues.push('');
    setDynamicFieldsValues(prevFieldsValues);


  };

  const handleFieldValueChange = (index:number, event:any) => {
    const prevFieldsValues:any[] = [...dynamicFieldsValues];
    //add field to array
    prevFieldsValues[index] = event.target.value;
    setDynamicFieldsValues(prevFieldsValues);
  }



    const handleNameChange = (event:any) => {
      setName(event.target.value);
    };

    const renderDynamicFields = () => {
      return dynamicFields.map((field, index) => (
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            margin: '10px',
            width: '100%',
          }}
        >
          <TextField
            key={index}
            label={field}
            placeholder='Enter value'
            fullWidth
            margin="normal"
            variant="outlined"
            value={dynamicFieldsValues[index]}
            onChange={(event) => handleFieldValueChange(index, event)}
          // Add any additional props or logic based on field name if needed
          />
          <br />
          <IconButton
            onClick={() => {
              const prevFields = [...dynamicFields];
              prevFields.splice(index, 1);
              setDynamicFields(prevFields);
              const prevFieldsValues = [...dynamicFieldsValues];
              prevFieldsValues.splice(index, 1);
              setDynamicFieldsValues(prevFieldsValues);
            }}
          >
            <Delete />
          </IconButton>

        </Box>));
    };

    return (
      <>
        <TableContainer component={Paper}>
          <Table sx={{ minWidth: 650 }} aria-label="simple table">
            <TableHead>
              <TableRow>
                <TableCell>Name</TableCell>
                <TableCell>Prefix</TableCell>
                <TableCell>Type</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {identifiers.map((identifier:any) => (
                <TableRow
                  key={identifier.name}
                  sx={{ '&:last-child td, &:last-child th': { border: 0 } }}
                  onClick={() => handleOpen(identifier)}
                  style={{ cursor: 'pointer' }}
                >
                  <TableCell component="th" scope="row">
                    {identifier.name}
                  </TableCell>
                  <TableCell>{identifier.prefix}</TableCell>
                  <TableCell>{Object.keys(identifier)[2]}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
        <Modal
          open={open}
          onClose={handleClose}
          aria-labelledby="modal-modal-title"
          aria-describedby="modal-modal-description"
        >
          {body}
        </Modal>
        <Modal open={openCreate} onClose={handleCloseCreate}>
          <Box
            sx={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              width: 400,
              bgcolor: 'background.paper',
              boxShadow: 24, p: 4,
            }}
          >
            <FormControl fullWidth margin="normal">
              <Select value={type} onChange={handleTypeChange}>
                <MenuItem value="salty">Salty</MenuItem>
                <MenuItem value="randy">Randy</MenuItem>
                <MenuItem value="group">Group</MenuItem>
              </Select>
            </FormControl>
            <TextField
              label="Name"
              placeholder='Enter name'
              value={name}
              onChange={handleNameChange}
              fullWidth
              margin="normal"
              variant="outlined"
            />
            <FormControl fullWidth margin="normal">
              <InputLabel id="demo-simple-select-label">Field</InputLabel>
              <Select value={selectedField} onChange={handleFieldChange}>
                <MenuItem value="transferable">transferable</MenuItem>
                <MenuItem value="isith">isith</MenuItem>
                <MenuItem value="nsith">nsith</MenuItem>
                <MenuItem value="wits">wits</MenuItem>
                <MenuItem value="toad">toad</MenuItem>
                <MenuItem value="proxy">proxy</MenuItem>
                <MenuItem value="delpre">delpre</MenuItem>
                <MenuItem value="dcode">dcode</MenuItem>
                <MenuItem value="data">data</MenuItem>
                <MenuItem value="pre">pre</MenuItem>
                <MenuItem value="states">states</MenuItem>
                <MenuItem value="rstates">rstates</MenuItem>
                <MenuItem value="prxs">prxs</MenuItem>
                <MenuItem value="nxts">nxts</MenuItem>
                <MenuItem value="mhab">mhab</MenuItem>
                <MenuItem value="keys">keys</MenuItem>
                <MenuItem value="ndigs">ndigs</MenuItem>
                <MenuItem value="bran">bran</MenuItem>
                <MenuItem value="count">count</MenuItem>
                <MenuItem value="ncount">ncount</MenuItem>
              </Select>
            </FormControl>
            {/* Add more buttons to add other fields as needed */}
            {renderDynamicFields()}
            <Button variant="contained" 
            //make onclick async for handlecomplete
            onClick= {async () => { 
              await handleComplete()
            }}

            // onClick={handleComplete}
            
            >
              Complete
            </Button>
          </Box>
        </Modal>
        <Fab
          color="primary"
          aria-label="add"
          style={{ position: 'fixed', bottom: '20px', right: '20px' }}
          // onClick={async () => {
          //   const length = identifiers.length.toString()
          //   await client.create(`aid${length}`, {})
          //   const list_identifiers = await client.list()
          //   setIdentifiers(list_identifiers)
          // }}
          onClick={handleOpenCreate}
        >
          <AddIcon />
        </Fab>
      </>
    );
  }


  //make it component 
  const CredentialsComponent = () => <div>Credentials Component</div>;
  const AidComponent = ({ data, text }:{data:any, text:string}) => {

    return (<Card sx={{ maxWidth: 545, marginX: 4 }}>
      <CardContent>
        <Typography variant="h6" component="div" gutterBottom>
          {text}
        </Typography>
        <Divider />
        <Grid container spacing={2}>
          {Object.entries(data).map(([key, value]) =>
            typeof value === 'string' ? (
              <Grid item xs={12} key={key}>
                <Typography variant="subtitle1" gutterBottom align='left'>
                  <strong>{tableObject[key].title}</strong> {value}
                </Typography>
              </Grid>
            ) : null
          )}
        </Grid>
      </CardContent>
    </Card>)
  }
  const ClientComponent = ({ client }:{client:SignifyClient|null}) => {
    //write an async function to get the client in the client component
    const [controller, setController] = useState(null)
    const [agent, setAgent] = useState(null)
    useEffect(() => {
      const getController = async () => {
        if (client !== null) {
          const controller = await client.state();
          setAgent(controller.agent)
          setController(controller.controller.state)
        }
      }
      getController();
    }
      , [client])
    return (
      agent !== null ?
        <>
          <Grid container >
            <AidComponent data={agent} text={'Agent'} />
            <AidComponent data={controller} text={'Controller'} />
          </Grid>


          <Divider />
          <Button variant="contained" color="primary" onClick={() => console.log('rotate')}>
            Rotate
          </Button>
        </>
        : <div key='identifiers'>Loading client data...</div>
    );

  };


  export default MainComponent;
