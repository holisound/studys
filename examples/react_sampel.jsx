// url query params
function useQuery() {
  return new URLSearchParams(useLocation().search);
}
let query = useQuery()
query.get('next')
// 未登录或登出 重定向
if (!this.props.user.isAuth){
    <Redirect
    to={{
      pathname: "/login",
      // search: "?next=" + encodeURI(`${location.pathname}`),
      search: `?next=${location.pathname}`,
      state: { from: location }
    }}
    />
}

//路由
    <Router>
      <div>
        <Switch>
          <Route path="/public">
            <PublicPage />
          </Route>
          <Route path="/login">
            <LoginPage />
          </Route>
          <PrivateRoute path="/protected">
            <ProtectedPage />
          </PrivateRoute>
        </Switch>
      </div>
    </Router>
