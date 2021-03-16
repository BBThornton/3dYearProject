import React, {useEffect, useRef, useState} from 'react';
import { Route, Switch,Redirect, BrowserRouter as Router } from "react-router-dom";
import ButtonAppBar from "./components/navbar";
import ExperimentCard from "./components/experiment_card";
import ExperimentConstructor from "./components/experiment_constructor";
/*
* Main page of the for contains all other components
* */

// "proxy": "http://backend:5000",

// useEffect(() => {
//     fetch("/api/get_data").then(response =>
//         response.json().then(data => {
//             console.log(data);
//         })
//     );
// }, []);

const App = () => (
    <Router>
        <Switch>
            <Route exact path="/" render={(props) =>
                <div id={"main_div"}>
                    <ButtonAppBar />
                    <div id={"content"}>
                        <h2> Update Testcell Default Values</h2>
                        <ExperimentCard {...props}/>
                    </div>
                </div>
                }/>
            <Route exact path="/builder" render={(props) =>
                    <div id={"main_div"}>
                        <ButtonAppBar />
                        <div id={"content"}>
                            <ExperimentConstructor {...props}/>
                        </div>
                    </div>
                }/>
        </Switch>
    </Router>
);

export default App;
