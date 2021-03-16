import React from 'react';
import Card from '@material-ui/core/Card';
import { Redirect } from "react-router-dom";
import Grid from "@material-ui/core/Grid";
import CardHeader from "@material-ui/core/CardHeader";
import CardContent from "@material-ui/core/CardContent";
import Button from "@material-ui/core/Button";

const data =
    [
        {
            id: 1,
            _id : "Manifest Creator" ,
            description: "Creates a Manifest",
            requirements: "none",
        },
        {
            id: 2,
            _id : "QA" ,
            description: "Quality analysis",
            requirements: "Manifest Creator",
        },
        {
            id: 3,
            _id : "Game Of Throne S01 E01" ,
            description: "THis is description",
            requirements: "Hi I am test content",
        }
    ];

const ExperimentCard = (props) =>{
    const { history } = props;
    var populate =
        <Grid
            container
            spacing={2}
            direction="row"
            justify="flex-start"
            alignItems="flex-start"
        >
        {data.map(function (value) {
        return(
            <Grid item xs={3} key={value.id}>
                {/*history.push(`/${value.id}`)*/}
                <Card onClick={()=>props.history.push({
                    pathname: '/builder', state: {id:value.id}
                })}>
                    <CardHeader
                        title={value._id}
                        subtitle={value.description}
                        actAsExpander={true}
                        showExpandableButton={true}
                    />
                    <CardContent expandable={true}>
                        {value.requirements}
                        <Button color="red" onClick={()=>console.log()}>
                            Run Experiment
                        </Button>
                    </CardContent>
                </Card>
            </Grid>
        )
        })}
    </Grid>;

    console.log(populate);

    return (
        <div>
            {populate}
        </div>
    );
}
export default ExperimentCard;
