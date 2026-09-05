import { NavLink } from "react-router-dom";

const links = [
  { to: "/", label: "1. Dataset Upload" },
  { to: "/overview", label: "2. OLAP Summary" },
  { to: "/analytics", label: "3. Churn Analytics" },
  { to: "/train", label: "4. Model Training" },
  { to: "/models", label: "5-7. Models & SHAP" },
  { to: "/predict/individual", label: "8. Individual Prediction" },
  { to: "/predict/batch", label: "9. Batch Prediction" },
  { to: "/history", label: "10. Prediction History" },
];

export default function Sidebar() {
  return (
    <div className="sidebar">
      <div className="brand"> Churn Predictor</div>
      {links.map((l) => (
        <NavLink
          key={l.to}
          to={l.to}
          end={l.to === "/"}
          className={({ isActive }) => "nav-link" + (isActive ? " active" : "")}
        >
          {l.label}
        </NavLink>
      ))}
    </div>
  );
}
