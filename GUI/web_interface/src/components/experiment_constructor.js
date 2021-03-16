import React,{useEffect, useRef, useState} from 'react';
import Card from '@material-ui/core/Card';
import CardContent from '@material-ui/core/CardContent';
import Button from '@material-ui/core/Button';
import CardHeader from "@material-ui/core/CardHeader";
import Grid from "@material-ui/core/Grid";
import Input from "@material-ui/core/Input";
import FormControl from "@material-ui/core/FormControl";
import InputLabel from "@material-ui/core/InputLabel";
import OutlinedInput from "@material-ui/core/OutlinedInput";

// const data = {
//     "_id": "Metadata_Creator",
//     "parent": "Manifest_Creator",
//     "input": null,
//     "output": {
//         "data": [
//             "metadata.tsv"
//         ],
//         "visuals": null
//     }
// }

// const [experimentID, setExperimentID] = useState("test");


const handleSubmit = (event) =>{
    console.log(event);
    event.preventDefault();
};

const ExperimentConstructor = (props) =>{
    console.log(props);

    return (
        <div>
            <h1>{props.location.state.id}</h1>

            <form noValidate autoComplete="off" onSubmit={handleSubmit}>
                <FormControl variant="outlined">
                    <InputLabel htmlFor="component-outlined">Name</InputLabel>
                    <OutlinedInput id="component-outlined" value="test" label="Name" />
                </FormControl>
                <Button type="submit">
                    Run
                </Button>
            </form>
        </div>
    );
};
export default ExperimentConstructor;
