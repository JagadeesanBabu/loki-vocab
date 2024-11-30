import React from 'react';
import { BrowserRouter as Router, Route, Switch } from 'react-router-dom';
import Quiz from './components/Quiz';
import Answer from './components/Answer';
import Summary from './components/Summary';
import Dashboard from './components/Dashboard';

function App() {
  return (
    <Router>
      <div className="App">
        <Switch>
          <Route path="/quiz" component={Quiz} />
          <Route path="/answer" component={Answer} />
          <Route path="/summary" component={Summary} />
          <Route path="/dashboard" component={Dashboard} />
        </Switch>
      </div>
    </Router>
  );
}

export default App;
