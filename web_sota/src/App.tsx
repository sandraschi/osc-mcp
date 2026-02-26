import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AppLayout } from '@/components/layout/app-layout';
import { Dashboard } from '@/pages/dashboard';
import { Control } from '@/pages/control';
import { Visualizer } from '@/pages/visualizer';
import { Chat } from '@/pages/chat';
import { Settings } from '@/pages/settings';
import { Ableton } from '@/pages/ableton';
import { TouchDesigner } from '@/pages/touchdesigner';
import { VRChat } from '@/pages/vrchat';
import { MaxMSP } from '@/pages/maxmsp';
import { SuperCollider } from '@/pages/supercollider';
import { Tools } from '@/pages/tools';
import { Apps } from './apps';
import { Help } from './help';
import { Status } from './status';
import { VCVRack } from './vcvrack';

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
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AppLayout>
    </Router>
  );
}

export default App;
