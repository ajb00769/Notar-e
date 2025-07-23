import { Component } from '@angular/core';
import {NgOptimizedImage} from "@angular/common";
import {Navbar} from "../../components/navbar/navbar";
import {Footer} from "../../components/footer/footer";
import {DashboardGreeter} from "../../components/dashboard-greeter/dashboard-greeter";
import {DashboardQuickActions} from "../../components/dashboard-quick-actions/dashboard-quick-actions";
import {DashboardCurrentDocuments} from "../../components/dashboard-current-documents/dashboard-current-documents";
import {DashboardBlockchainStatus} from "../../components/dashboard-blockchain-status/dashboard-blockchain-status";
import {DashboardAppointments} from "../../components/dashboard-appointments/dashboard-appointments";
import {DashboardHelp} from "../../components/dashboard-help/dashboard-help";

@Component({
  selector: 'app-dashboard',
    imports: [
        Navbar,
        Footer,
        DashboardGreeter,
        DashboardQuickActions,
        DashboardCurrentDocuments,
        DashboardBlockchainStatus,
        DashboardAppointments,
        DashboardHelp
    ],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.scss'
})
export class Dashboard {

}
