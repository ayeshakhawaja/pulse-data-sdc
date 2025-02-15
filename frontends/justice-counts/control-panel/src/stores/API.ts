// Recidiviz - a data platform for criminal justice reform
// Copyright (C) 2022 Recidiviz, Inc.
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.
// =============================================================================

import { makeAutoObservable, runInAction, when } from "mobx";

import { trackLoadTime, trackNetworkError } from "../analytics";
import { AuthStore } from "../components/Auth";
import { showToast } from "../components/Toast";

export interface RequestProps {
  path: string;
  method: "GET" | "POST" | "PUT" | "DELETE" | "PATCH";
  body?: FormData | Record<string, unknown>;
  retrying?: boolean;
}

class API {
  authStore: AuthStore;

  isSessionInitialized: boolean;

  csrfToken: string;

  constructor(authStore: AuthStore) {
    makeAutoObservable(this);

    this.authStore = authStore;
    this.isSessionInitialized = false;
    this.csrfToken = "";

    when(
      () => authStore.isAuthorized,
      () => this.initSession()
    );
  }

  async initSession(): Promise<void | string> {
    try {
      const response = (await this.request({
        path: "/api/init",
        method: "GET",
      })) as Response;
      const { csrf } = await response.json();

      runInAction(() => {
        if (csrf !== "") this.csrfToken = csrf;
        this.isSessionInitialized = true;
      });
    } catch (error) {
      if (error instanceof Error) return error.message;
      return String(error);
    }
  }

  async request({
    path,
    method,
    body,
    retrying = false,
  }: RequestProps): Promise<Body | Response | string> {
    try {
      const startTime = Date.now();
      if (!this.authStore.getToken) {
        return Promise.reject();
      }

      const token = await this.authStore.getToken();

      // Files are sent as FormData and not JSON
      const jsonOrFormDataBody =
        body instanceof FormData ? body : JSON.stringify(body);

      const headers: HeadersInit = {
        Authorization: `Bearer ${token}`,
        "X-CSRF-Token": this.csrfToken,
      };

      if (!(body instanceof FormData)) {
        headers["Content-Type"] = "application/json";
      }

      const response = await fetch(path, {
        body: method !== "GET" ? jsonOrFormDataBody : null,
        method,
        headers,
      });

      if (response.status >= 400) {
        if (!retrying) {
          const responseText = await response.clone().text();

          if (responseText.includes("The CSRF token has expired.")) {
            await this.initSession();
            return runInAction(() =>
              this.request({ path, method, body, retrying: true })
            );
          }
        }

        const responseCopy = response.clone();
        const responseJson = await responseCopy.json();
        trackNetworkError(
          path,
          method,
          response.status,
          responseJson.description
        );
      } else {
        const loadTime = Date.now() - startTime;
        trackLoadTime(path, method, loadTime);
      }

      return response;
    } catch (error) {
      if (error instanceof Error) {
        trackNetworkError(path, method, 0, error.message);
        if (error.message.includes("Login required")) {
          showToast(
            "Your session has expired. Redirecting you to the login page...",
            false,
            "red"
          );
          // Wait before reloading so user has a chance to see the toast
          setTimeout(() => {
            window.location.reload();
          }, 1000);
        }
        throw error;
      }
      trackNetworkError(path, method, 0, String(error));
      throw error;
    }
  }
}

export default API;
