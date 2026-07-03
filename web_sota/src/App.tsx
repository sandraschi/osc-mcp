import { AppLayout } from "@/components/layout/app-layout";
import Logging from "@/pages/Logging";
import { Ableton } from "@/pages/ableton";
import { Apps } from "@/pages/apps";
import { Chat } from "@/pages/chat";
import { Control } from "@/pages/control";
import { Dashboard } from "@/pages/dashboard";
import { Help } from "@/pages/help";
import { MaxMSP } from "@/pages/maxmsp";
import { Settings } from "@/pages/settings";
import { Status } from "@/pages/status";
import { SuperCollider } from "@/pages/supercollider";
import { Tools } from "@/pages/tools";
import { TouchDesigner } from "@/pages/touchdesigner";
import { VCVRack } from "@/pages/vcvrack";
import { Visualizer } from "@/pages/visualizer";
import { VRChat } from "@/pages/vrchat";
import {
  Navigate,
  Route,
  BrowserRouter as Router,
  Routes,
} from "react-router-dom";

function App() {
  return (
    <Router>
      <AppLayout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/apps" element={<Apps />} />
          <Route path="/status" element={<Status />} />
          <Route path="/control" element={<Control />} />
          <Route path="/visualizer" element={<Visualizer />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/help" element={<Help />} />
          <Route path="/ableton" element={<Ableton />} />
          <Route path="/touchdesigner" element={<TouchDesigner />} />
          <Route path="/vrchat" element={<VRChat />} />
          <Route path="/maxmsp" element={<MaxMSP />} />
          <Route path="/supercollider" element={<SuperCollider />} />
          <Route path="/vcvrack" element={<VCVRack />} />
          <Route path="/tools" element={<Tools />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/logs" element={<Logging />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AppLayout>
    </Router>
  );
}

export default App;
