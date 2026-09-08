import pandas as pd
from .analytical_contracts import AnalyticalRequest, CapabilityResult, AnalysisRunEnvelope

class MLPredictAdapter:
    @staticmethod
    def run(request: AnalyticalRequest, run_envelope: AnalysisRunEnvelope) -> CapabilityResult:
        try:
            from sklearn.linear_model import Ridge
            from sklearn.model_selection import train_test_split
            from sklearn.metrics import root_mean_squared_error, r2_score
        except ImportError:
            return CapabilityResult(request_id=request.id, success=False, error="scikit-learn missing")
            
        df = request.dataset.copy()
        y_col = request.command.dependent_var
        x_cols = request.command.independent_vars
        
        if not y_col or not x_cols:
            return CapabilityResult(request_id=request.id, success=False, error="ML predict requires dependent and independent variables.")
            
        df = df.dropna(subset=[y_col] + list(x_cols))
        
        X = df[x_cols]
        y = df[y_col]
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        model = Ridge(alpha=1.0)
        model.fit(X_train, y_train)
        
        preds = model.predict(X_test)
        rmse = root_mean_squared_error(y_test, preds)
        r2 = r2_score(y_test, preds)
        
        feat_imp = pd.DataFrame({
            "Feature": x_cols,
            "Importance (Ridge Coef)": model.coef_
        }).sort_values("Importance (Ridge Coef)", key=abs, ascending=False)
        
        messages = [
            f"ML Prediction (Ridge) executed.",
            f"Train N={len(X_train)}, Test N={len(X_test)}",
            f"Test RMSE: {rmse:.4f}",
            f"Test R-squared: {r2:.4f}"
        ]
        
        return CapabilityResult(
            request_id=request.id,
            success=True,
            display_tables={"Feature Importance": feat_imp},
            run_envelope=run_envelope,
            messages=messages,
            internal_data={"model": model, "rmse": rmse, "r2": r2}
        )
